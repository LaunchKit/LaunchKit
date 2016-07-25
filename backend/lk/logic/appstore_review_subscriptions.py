# encoding: utf-8
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
from datetime import datetime

from backend.lk.logic import appstore
from backend.lk.logic import appstore_app_info
from backend.lk.logic import appstore_review_notify
from backend.lk.models import AppStoreApp
from backend.lk.models import AppStoreAppInterest
from backend.lk.models import AppStoreReview
from backend.lk.models import AppStoreReviewSubscription


def create_email_subscription(user, email):
  subs = AppStoreReviewSubscription.objects.filter(user=user)
  subs = list(subs.extra(where=["data->'email'=%s"], params=[email]))
  if subs:
    sub = subs[0]
  else:
    sub = AppStoreReviewSubscription(user=user)
    sub.email = email

  if sub.enabled:
    # Already have this sub.
    return None

  sub.enabled = True
  if sub.last_notification_time:
    # Move pointer to now so they don't get a deluge of reviews.
    sub.last_notification_time = datetime.now()
  sub.save()

  my_apps = appstore.mark_should_track_reviews_for_my_apps(user)
  appstore_review_notify.send_new_subscription_email(sub, my_apps)

  return sub


def create_my_email_subscription(user):
  subs = AppStoreReviewSubscription.objects.filter(user=user)
  subs = list(subs.extra(where=["data->'my_email'='1'"]))
  if subs:
    sub = subs[0]
  else:
    sub = AppStoreReviewSubscription(user=user)
    sub.my_email = True

  if sub.enabled:
    # Already have this sub.
    return None

  sub.enabled = True
  if sub.last_notification_time:
    # Move pointer to now so they don't get a deluge of reviews.
    sub.last_notification_time = datetime.now()
  sub.save()

  # Note: No subscription review notification because they get a
  # "Reviews ready" email in a little bit.
  appstore.mark_should_track_reviews_for_my_apps(user)

  return sub


def create_slack_subscription(user, slack_url):
  subs = AppStoreReviewSubscription.objects.filter(user=user)
  subs = list(subs.extra(where=["data->'slack_url'=%s"], params=[slack_url]))
  if subs:
    sub = subs[0]
  else:
    sub = AppStoreReviewSubscription(user=user)
    sub.slack_url = slack_url

  if sub.enabled:
    # Already have this sub.
    return None

  sub.enabled = True
  if sub.last_notification_time:
    # Move pointer to now so they don't get a deluge of reviews.
    sub.last_notification_time = datetime.now()
  sub.save()

  my_apps = appstore.mark_should_track_reviews_for_my_apps(user)
  appstore_review_notify.send_slack_subscription_configured_message(sub, my_apps)

  return sub


def create_slack_channel_subscription(user, slack_channel_name):
  subs = AppStoreReviewSubscription.objects.filter(user=user)
  subs = list(subs.extra(where=["data->'slack_channel_name'=%s"], params=[slack_channel_name]))
  if subs:
    sub = subs[0]
  else:
    sub = AppStoreReviewSubscription(user=user)

  if sub.enabled:
    # Already have this sub.
    return None

  sub.slack_channel_name = slack_channel_name
  sub.enabled = True

  if sub.last_notification_time:
    # Move pointer to now so they don't get a deluge of reviews.
    sub.last_notification_time = datetime.now()
  sub.save()

  my_apps = appstore.mark_should_track_reviews_for_my_apps(user)
  appstore_review_notify.send_slack_subscription_configured_message(sub, my_apps)

  return sub


def subscribed_slack_channel_names(user):
  subs = AppStoreReviewSubscription.objects.filter(user=user, enabled=True)
  subs = list(subs.extra(where=["(data->'slack_channel_name')::text IS NOT NULL"]))
  return [sub.slack_channel_name for sub in subs]


def invalidate_slack_channel_subscriptions(user):
  AppStoreReviewSubscription.objects \
      .filter(user=user) \
      .extra(where=["(data->'slack_channel_name')::text IS NOT NULL"]) \
      .update(enabled=False)


def create_twitter_subscription_from_connection(twitter_connection):
  user = twitter_connection.user
  app = twitter_connection.app

  # FIXME: Add "country" to filter_app subs.
  interest = AppStoreAppInterest.objects.filter(user=user, app=app)[0]
  appstore_app_info.decorate_app(app, interest.country)

  twitter_handle = twitter_connection.handle

  if twitter_handle not in user.twitter_handles:
    return None

  subs = AppStoreReviewSubscription.objects.filter(user=user, filter_app=app, twitter_connection=twitter_connection)
  if subs:
    sub = subs[0]
    sub.filter_app = app
  else:
    sub = AppStoreReviewSubscription(user=user)
    sub.filter_app = app
    sub.twitter_connection = twitter_connection
    mark_subscription_filtered_very_good(sub, True)

  if sub.enabled:
    # Already have this sub.
    return None

  sub.enabled = True
  if sub.last_notification_time:
    # Move pointer to now so they don't get a deluge of reviews.
    sub.last_notification_time = datetime.now()
  sub.save()

  appstore.mark_should_track_reviews_for_my_apps(user)

  return sub


def get_user_subscription_by_encrypted_id(user, encrypted_sub_id):
  sub = AppStoreReviewSubscription.find_by_encrypted_id(encrypted_sub_id)
  if sub and sub.user_id == user.id and sub.enabled:
    return sub
  return None


def disable_subscription(subscription):
  subscription.enabled = False
  subscription.save()

  appstore.maybe_disable_review_tracking_for_my_apps(subscription.user)


def mark_subscription_filtered_good(subscription, do_filter):
  subscription.filter_good = (do_filter and 1) or 0
  subscription.save()


def mark_subscription_filtered_very_good(subscription, do_filter):
  subscription.filter_very_good = (do_filter and 1) or 0
  subscription.save()


def subscriptions_for_user(user):
  my_subs = (
      AppStoreReviewSubscription.objects
      .filter(user=user, enabled=True)
      .select_related('filter_app', 'twitter_connection')
  )
  for sub in my_subs:
    if sub.filter_app_id:
      # FIXME: Add "country" to filter_app subs.
      interests = AppStoreAppInterest.objects.filter(user_id=user.id, app_id=sub.filter_app_id)[:1]
      appstore_app_info.decorate_app(sub.filter_app, interests[0].country)
  return my_subs


def subscribed_reviews_for_user(user, app=None, start_review=None, rating=None, limit=None, country=None):
  if not limit:
    limit = 25

  interested_apps = AppStoreAppInterest.objects.filter(user=user, enabled=True).values_list('app_id', 'country')
  if app:
    interested_apps = interested_apps.filter(app=app)
  if country:
    interested_apps = interested_apps.filter(country=country)

  interested_apps = list(interested_apps)
  if not interested_apps:
    return []

  matching_apps_by_country = {}
  for app_id, country in interested_apps:
    if country not in matching_apps_by_country:
      matching_apps_by_country[country] = []
    matching_apps_by_country[country].append(app_id)

  where_ors = []
  params = []
  for country, app_ids in matching_apps_by_country.items():
    where_ors.append('country = %%s AND app_id IN (%s)' % ','.join(['%s'] * len(app_ids)))
    params.append(country)
    params += app_ids
  where = '((%s))' % ') OR ('.join(where_ors)

  if rating:
    where += ' AND rating = %s'
    params.append(rating)

  if start_review:
    where += ' AND appstore_review_id < %s'
    params.append(start_review.appstore_review_id)

  params.append(limit)

  reviews = AppStoreReview.objects.raw("""
    WITH reviews AS (
      SELECT * FROM lk_appstorereview WHERE
        invalidated_time IS NULL AND (%s)
    )
    SELECT * FROM reviews ORDER BY appstore_review_id DESC LIMIT %%s
  """ % where, params)
  reviews = list(reviews)

  app_ids = set(r.app_id for r in reviews)
  apps = AppStoreApp.objects.filter(id__in=list(app_ids))
  apps_by_id = dict((a.id, a) for a in apps)

  for r in reviews:
    r.app = apps_by_id[r.app_id]
    appstore_app_info.decorate_app(r.app, r.country)

  return reviews
