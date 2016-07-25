#
# Copyright 2016 Cluster Labs, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import logging
import math
import time
from datetime import datetime
from datetime import timedelta

from Crypto.Random import random
from django.db import IntegrityError
from django.db import connection
from django.db import transaction
from django.db.models import F
from django.db.models import Q
from redis import WatchError

from backend.lk.logic import appstore_app_info
from backend.lk.logic import appstore_review_fetch
from backend.lk.logic import appstore_review_notify
from backend.lk.logic import emails
from backend.lk.logic import redis_wrap
from backend.lk.models import AppStoreApp
from backend.lk.models import AppStoreAppInterest
from backend.lk.models import AppStoreAppReviewTracker
from backend.lk.models import AppStoreReview
from backend.lk.models import User
from backend import celery_app


WAIT_BETWEEN_PAGES = 0.5


#
# UPDATE REVIEW OBJECTS
#


def filter_new_reviews(appstore_app, fetched_reviews):
  review_ids = [review.appstore_review_id for review in fetched_reviews]
  existing_review_ids = AppStoreReview.objects.filter(appstore_review_id__in=review_ids
      ).values_list('appstore_review_id', flat=True).distinct()
  existing_review_ids = set(existing_review_ids)

  return [r for r in fetched_reviews
          if r.appstore_review_id not in existing_review_ids]


TOTAL_PAGES = 10


def update_with_new_reviews(appstore_app, country):
  total_to_insert = []

  failed_pages = 0
  successful_pages = 0
  did_fail_altogether = False
  tracker = AppStoreAppReviewTracker.objects.get(app_id=appstore_app.id, country=country)

  # Important: Include "current_version_reviews_count" here because reviews_count might be wrong.
  reviews_count = max(appstore_app.reviews_count, appstore_app.current_version_reviews_count)
  guessed_pages = int(math.ceil(reviews_count / 50.0))

  for page in range(min(TOTAL_PAGES, guessed_pages)):
    # Don't hammer the site esp on initial ingestion.
    time.sleep(WAIT_BETWEEN_PAGES)

    has_next_page, fetched_reviews = appstore_review_fetch.fetch_reviews(appstore_app,
        country=country, page=(page + 1))

    if fetched_reviews is None:
      failed_pages += 1
      if failed_pages == 3:
        if successful_pages == 0:
          did_fail_altogether = True
        break
      else:
        continue

    successful_pages += 1

    insert = filter_new_reviews(appstore_app, fetched_reviews)
    total_to_insert += insert

    if len(insert) < len(fetched_reviews) and tracker.has_had_full_ingestion:
      # Less than the whole page was inserted, so we don't need to keep going
      # back in history.
      break

    if not has_next_page:
      break

  if failed_pages == 0 and successful_pages > 0 and not tracker.has_had_full_ingestion:
    tracker.has_had_full_ingestion = True
    tracker.save(update_fields=['has_had_full_ingestion'])

  if did_fail_altogether:
    return -1, 0

  if not total_to_insert:
    return 0, 0

  # Reverse these so they get inserted in time order where create_time
  # is ever so slightly newer for newer reviews.
  total_to_insert.reverse()
  total_inserts_were_updates = 0

  present = set([])
  total_to_insert_deduped = []
  for r in total_to_insert:
    if r.appstore_review_id in present:
      # Sometimes dupes exist across pages.
      continue
    total_to_insert_deduped.append(r)
    present.add(r.appstore_review_id)

  total_to_insert = total_to_insert_deduped

  with transaction.atomic():
    author_ids = AppStoreReview.objects.filter(app_id=appstore_app.id, country=country,
        author_id__in=[r.author_id for r in total_to_insert]).values_list('author_id', flat=True).distinct()
    author_ids = set(author_ids)
    # This is len(unique(author_ids)) because multiple author ids won't appear in the same feed.
    total_inserts_were_updates = len(author_ids)

    for review in total_to_insert:
      if not tracker.successful_ingestion_attempts:
        # Never ingested before.
        review.initial_ingestion = True
      elif review.appstore_review_id < (tracker.latest_appstore_review_id or 0):
        # Ingested before, but this review is older.
        review.initial_ingestion = True
      else:
        review.initial_ingestion = False

      review.author_reviewed_before = review.author_id in author_ids

    logging.info('Inserting %s reviews for app %s (%s)',
        len(total_to_insert), appstore_app.bundle_id, appstore_app.id)
    try:
      AppStoreReview.objects.bulk_create(total_to_insert)
    except IntegrityError:
      logging.info('Bulk create got integrity problem, ignoring for now...')
      return 0, 0

    if author_ids:
      AppStoreReview.objects.filter(app_id=appstore_app.id, country=country, author_id__in=list(author_ids),
          invalidated_time__isnull=True).update(invalidated_time=datetime.now())

    cursor = connection.cursor()
    cursor.execute("""
      UPDATE lk_appstoreappreviewtracker SET latest_appstore_review_id = (
        SELECT MAX(appstore_review_id) FROM lk_appstorereview WHERE app_id=%s AND country=%s)
      WHERE app_id=%s AND country=%s
    """, [appstore_app.id, country, appstore_app.id, country])

  return len(total_to_insert), total_inserts_were_updates


#
# PERIODIC NOTIFICATION PIPELINE
#


APP_REVIEWS_INGESTION_ZSET_KEY = 'review-ingestion-app-ids-countries'
HOUR = (60.0 * 60.0)


def next_ingestion_time(app, country):
  appstore_app_info.decorate_app(app, country)
  reviews_count = app.reviews_count or 0

  if reviews_count < 100:
    # Few times a day, ish.
    base_wait = HOUR * 6
  elif reviews_count < 1000:
    # Every 3 hours, ish.
    base_wait = HOUR * 2
  else:
    # Every 1.5 hours, ish.
    base_wait = HOUR

  wait = base_wait + (base_wait * (random.randint(0, 100) / 100.0))
  return time.time() + wait


def mark_app_needs_ingestion(app, country, force=False):
  t = AppStoreAppReviewTracker.objects.get(app_id=app.id, country=country)
  if not force and t.last_ingestion_time:
    return

  # If it needs ingestion, do it now.
  target_time = time.time()

  # ADD app.id TO ZSET AT target_time
  redis = redis_wrap.client()
  redis.zadd(APP_REVIEWS_INGESTION_ZSET_KEY, target_time, '%s:%s' % (app.id, country))


def add_all_apps_to_ingestion_queue():
  apps_countries = list(AppStoreAppReviewTracker.objects.all().values_list('app_id', 'country'))
  redis = redis_wrap.client()
  for app_id, country in apps_countries:
    app = AppStoreApp.objects.get(pk=app_id)
    appstore_app_info.decorate_app(app, country)
    target_time = next_ingestion_time(app, country)
    redis.zadd(APP_REVIEWS_INGESTION_ZSET_KEY, target_time, '%s:%s' % (app_id, country))


def ingest_app(app, country):
  appstore_app_info.decorate_app(app, country)

  # Check current_version_reviews_count here too because apparently total
  # reviews count can be missing sometimes, but current version is present.
  if app.reviews_count > 0 or app.current_version_reviews_count > 0:
    try:
      inserted, _ = update_with_new_reviews(app, country)
      if inserted > 0:
        appstore_review_notify.notify_subscriptions_for_app(app, country)

    except appstore_review_fetch.RateLimitedError:
      # This should stop other apps from being ingested in this run as well.
      raise

    except Exception:
      logging.exception('Problem ingesting reviews for app id: %s (%s - %s)',
          app.id, app.itunes_id, app.bundle_id)
      return

  else:
    # No reviews in the store, no need to check.
    inserted = 0

  tracker_qs = AppStoreAppReviewTracker.objects.filter(app_id=app.id, country=country)
  if inserted < 0:
    # A value of -1 indicates that something went wrong and ingestion failed.
    tracker_qs.update(
        failed_ingestion_attempts=F('failed_ingestion_attempts') + 1,
        last_ingestion_time=datetime.now())
  else:
    tracker_qs.update(
        successful_ingestion_attempts=F('successful_ingestion_attempts') + 1,
        last_ingestion_time=datetime.now())


def apps_countries_to_ingest(limit, now_offset=0):
  now_timestamp = time.time() + now_offset

  apps_needing_ingestion = []
  countries = []

  # Atomically find next app ids to check.
  redis = redis_wrap.client()
  while True:
    with redis.pipeline() as pipe:
      try:
        pipe.watch(APP_REVIEWS_INGESTION_ZSET_KEY)
        app_ids_countries_needing_ingestion = pipe.zrangebyscore(APP_REVIEWS_INGESTION_ZSET_KEY,
            0, now_timestamp,
            start=0, num=limit)

        if app_ids_countries_needing_ingestion:
          app_ids = []
          countries = []
          for ac in app_ids_countries_needing_ingestion:
            app_id, country = ac.split(':')
            app_id = long(app_id)
            app_ids.append(app_id)
            countries.append(country)

          apps_by_id = dict((a.id, a) for a in AppStoreApp.objects.filter(id__in=app_ids))
          apps_needing_ingestion = [apps_by_id[app_id] for app_id in app_ids]

          rescored_app_ids = []
          for app, country in zip(apps_needing_ingestion, countries):
            rescored_app_ids.append(next_ingestion_time(app, country))
            rescored_app_ids.append('%s:%s' % (app.id, country))

          if rescored_app_ids:
            pipe.multi()
            pipe.zadd(APP_REVIEWS_INGESTION_ZSET_KEY, *rescored_app_ids)
            pipe.execute()

        break
      except WatchError:
        logging.info('Interrupted while fetching app ids to ingest...')

  for app, country in zip(apps_needing_ingestion, countries):
    yield app, country


def maybe_ingest_reviews(now_offset=0):
  # Used by tests
  for app, country in apps_countries_to_ingest(30, now_offset=now_offset):
    ingest_app(app, country)



@celery_app.task(ignore_result=True)
def maybe_send_reviews_ready_emails():
  nonready_interests = AppStoreAppInterest.objects.filter(ready=False)
  nonready_app_ids_countries = nonready_interests.values_list('app_id', 'country').distinct()

  matching_apps = Q(app_id=-1)
  for app_id, country in nonready_app_ids_countries:
    matching_apps |= Q(app_id=app_id, country=country)

  ready_condition = Q(successful_ingestion_attempts__gt=0) | Q(failed_ingestion_attempts__gte=3)

  ready_apps_with_nonready_interests = AppStoreAppReviewTracker.objects.filter(
      ready_condition, matching_apps).values_list('app_id', 'country')

  ready_apps = Q(app_id=-1)
  for app_id, country in ready_apps_with_nonready_interests:
    ready_apps |= Q(app_id=app_id, country=country)

  user_ids_with_nonready_interests_remaining = nonready_interests.exclude(
      ready_apps).values_list('user_id', flat=True).distinct()

  ready_user_ids = nonready_interests.exclude(
      user_id__in=user_ids_with_nonready_interests_remaining).values_list('user_id', flat=True).distinct()
  ready_users = list(User.objects.filter(id__in=ready_user_ids))

  if len(ready_users) > 50:
    logging.warn('Lots of ready users, this should be optimized...')

  for user in ready_users:
    ready_interests_batch = AppStoreAppInterest.objects.filter(ready=False, user_id=user.id)
    # NOTE: Do this before updating, otherwise delayed SQL execution means
    # our list is returned empty.
    app_ids_countries = list(ready_interests_batch.values_list('app_id', 'country'))
    ready_interests_batch.update(ready=True)

    if not user.flags.any_reviews_ready:
      user.set_flags(['any_reviews_ready'])

    if app_ids_countries:
      send_reviews_ready_email.delay(user.id, app_ids_countries)
    else:
      logging.warn('WTF? no app ids to notify this user about (%s)', user.id)


@celery_app.task(ignore_result=True)
def send_reviews_ready_email(user_id, app_ids_countries):
  user = User.objects.get(pk=user_id)
  app_ids = [app_id for app_id, _ in app_ids_countries]
  apps_by_id = dict((a.id, a) for a in AppStoreApp.objects.filter(id__in=app_ids))

  apps = []
  for app_id, country in app_ids_countries:
    app = apps_by_id[app_id]
    appstore_app_info.decorate_app(app, country)
    apps.append(app)

  messsage = emails.create_reviews_ready_email(user, apps)
  emails.send_all([messsage])
