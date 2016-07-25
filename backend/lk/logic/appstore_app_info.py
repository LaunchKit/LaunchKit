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
import time
from datetime import datetime

from Crypto.Random import random
from django.db import InternalError
from redis import WatchError

from backend.lk.logic import appstore_fetch
from backend.lk.logic import redis_wrap
from backend.lk.models import AppStoreApp
from backend.lk.models import AppStoreAppInfo
from backend.lk.models import AppStoreAppRating
from backend import celery_app


def decorate_app(app, country):
  if app.decorated_info and app.decorated_country == country:
    return

  app_info = _latest_app_info_by_id(app.id, country)
  if not app_info:
    raise ValueError('Could not find app info with that id+country (%s+%s)' % (app.id, country))
  app.decorated_country = country
  app.decorated_info = app_info


PROPERTIES_TO_CHECK = [
  'name',
  'description',
  'release_notes',

  'version',

  'icon_60',
  'icon_100',
  'icon_512',

  'category',

  'price',
  'currency',

  'size_bytes',

  'rating',
  'reviews_count',

  'current_version_rating',
  'current_version_reviews_count',

  'content_rating',

  'developer_id',
  'developer_url',
  'developer_name',

  'categories',
  'screenshots',
  'ipad_screenshots',

  'release_date',
]

PROPERTIES_CAUSING_RATING_UPDATE = [
  'rating',
  'reviews_count',

  'current_version_rating',
  'current_version_reviews_count',
]

PROPERTIES_CAUSING_UPDATE = PROPERTIES_CAUSING_RATING_UPDATE + [
  # These change arbitrarily all the time with new "download URLs"
  'icon_60',
  'icon_100',
  'icon_512',
]


def _latest_app_info_by_id(app_id, country):
  app_info = list(AppStoreAppInfo.objects.filter(app_id=app_id, country=country).order_by('-create_time')[:1])
  if app_info:
    return app_info[0]
  return None


def fetch_info_and_maybe_update_app(app, country):
  fetched_app_info = appstore_fetch.app_info_with_id(app.itunes_id, country)
  if not fetched_app_info:
    # TODO(Taylor): Increment some counter or something so we can stop checking this thing eventually.
    logging.info('App removed or otherwise not available: %s (%s)', app.itunes_id, app.bundle_id)
    return

  try:
    update_app_info_with_fetched_data(app, fetched_app_info)
  except InternalError as e:
    logging.info('Could not update app info: %s app info: %s', e, fetched_app_info.__dict__)


def update_app_info_with_fetched_data(app, fetched_app_info):
  saved_app_info = _latest_app_info_by_id(app.id, fetched_app_info.country)

  insert, update, rating_update = False, False, False
  changed_properties = []

  if not saved_app_info:
    # No record yet.
    insert = True
    rating_update = True
  else:
    for prop in PROPERTIES_TO_CHECK:
      if getattr(saved_app_info, prop) != getattr(fetched_app_info, prop):
        changed_properties.append(prop)
        if prop in PROPERTIES_CAUSING_UPDATE:
          setattr(saved_app_info, prop, getattr(fetched_app_info, prop))
          update = True
          if prop in PROPERTIES_CAUSING_RATING_UPDATE:
            rating_update = True
        else:
          insert = True

  if any([insert, update, rating_update]):
    logging.info('Updated properties for app %s (%s): %s',
        app.id, app.bundle_id, changed_properties)

  if insert:
    fetched_app_info.app = app
    fetched_app_info.save()

  elif update:
    saved_app_info.save()

  if rating_update:
    rating = AppStoreAppRating(app=app)
    for prop in PROPERTIES_CAUSING_RATING_UPDATE:
      setattr(rating, prop, getattr(fetched_app_info, prop))
    rating.save()

  return insert or update


#
# PERIODIC APP INGESTION PIPELINE
#


APP_INFO_INGESTION_ZSET_KEY = 'info-ingestion-app-ids'


def next_ingestion_time():
  HALF_HOUR = (30.0 * 60.0)
  return time.time() + (HALF_HOUR * 12) + (HALF_HOUR * (random.randint(0, 100) / 100.0))


def mark_app_needs_info_ingestion(app):
  target_time = time.time()

  # ADD app.id TO ZSET AT target_time
  redis = redis_wrap.client()
  redis.zadd(APP_INFO_INGESTION_ZSET_KEY, target_time, app.id)


@celery_app.task(ignore_result=True, queue='appstore')
def maybe_ingest_app_info(now_offset=0):
  now_timestamp = time.time() + now_offset

  app_ids_needing_ingestion = []

  # Atomically find next app ids to check.
  redis = redis_wrap.client()
  while True:
    with redis.pipeline() as pipe:
      try:
        pipe.watch(APP_INFO_INGESTION_ZSET_KEY)
        app_ids_needing_ingestion = pipe.zrangebyscore(APP_INFO_INGESTION_ZSET_KEY,
            0, now_timestamp,
            start=0, num=30)

        if app_ids_needing_ingestion:
          rescored_app_ids = []
          for app_id in app_ids_needing_ingestion:
            rescored_app_ids.append(next_ingestion_time())
            rescored_app_ids.append(app_id)
          pipe.multi()
          pipe.zadd(APP_INFO_INGESTION_ZSET_KEY, *rescored_app_ids)
          pipe.execute()

        break
      except WatchError:
        logging.info('Interrupted while fetching app ids to ingest...')

  if not app_ids_needing_ingestion:
    return

  logging.info('Ingesting app infos for %d app(s)...', len(app_ids_needing_ingestion))
  for app_id in app_ids_needing_ingestion:
    try:
      app = AppStoreApp.objects.get(pk=app_id)
    except AppStoreApp.DoesNotExist:
      logging.warn('Deleted app id, removing from ingestion queue: %s', app_id)
      redis.zrem(APP_INFO_INGESTION_ZSET_KEY, app_id)
      continue

    # NOTE: This should be unique but it isn't right now for whatever reason.
    unique_countries = set(app.app_info_countries)
    for country in unique_countries:
      try:
        fetch_info_and_maybe_update_app(app, country)

      except appstore_fetch.RateLimitedError:
        # This is not likely to fix itself soon. Give up.
        logging.info('Rate limited by App Store, giving up for now...')
        time.sleep(15)
        return

      except Exception:
        logging.exception('Problem ingesting app info for app id: %s - %s (%s - %s)',
            app.id, country, app.itunes_id, app.bundle_id)

    app.app_info_ingestion_time = datetime.now()
    app.save(update_fields=['app_info_ingestion_time'])

    time.sleep(0.3333)
