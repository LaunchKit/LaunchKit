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
import time
from backend.util import text

from django.conf import settings
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.db.models import Count
from django.db.models import Max
from django.db.models import Q

from backend.lk.logic import appstore_app_info
from backend.lk.logic import emails
from backend.lk.logic import crypto_hack
from backend.lk.logic import slack
from backend.lk.logic import twitter
from backend.lk.models import AppStoreApp
from backend.lk.models import AppStoreAppInterest
from backend.lk.models import AppStoreReview
from backend.lk.models import AppStoreReviewNotification
from backend.lk.models import AppStoreReviewSubscription
from backend.lk.models import User
from backend.util import urlutil
from backend import celery_app


#
# SEND NEW REVIEWS TO SUBSCRIPTIONS
#


def notify_subscriptions_for_app(app, country):
  _maybe_notify_subscriptions_for_app_id.delay(app.id, country)


@celery_app.task(ignore_result=True)
def _maybe_notify_subscriptions_for_app_id(app_id, country):
  app = AppStoreApp.objects.get(pk=app_id)
  appstore_app_info.decorate_app(app, country)

  interested_parties = AppStoreAppInterest.objects.filter(app_id=app.id, country=country, enabled=True).values_list('user_id', flat=True)
  subs = AppStoreReviewSubscription.objects.filter(user__in=interested_parties, enabled=True).select_related('user')
  # Restrict subs to unfiltered or filtered just for this app.
  subs = subs.filter(Q(filter_app_id__isnull=True) | Q(filter_app_id=app_id))

  if subs.count() > 100:
    logging.warn('Optimize subscription sending for app: %s (%s - %s)',
        app.id, app.itunes_id, app.bundle_id)

  email_messages = []
  notifications = []

  for sub in subs:
    reviews = AppStoreReview.objects.filter(app=app, initial_ingestion=False,
        create_time__gt=(sub.last_notification_time or sub.create_time),
        country=country)
    if sub.filter_good:
      reviews = reviews.filter(rating__gte=4)
    if sub.filter_very_good:
      reviews = reviews.filter(rating=5)

    reviews_stats = reviews.aggregate(max_create_time=Max('create_time'), count=Count('id'))
    reviews_count = reviews_stats['count']
    reviews_max_create_time = reviews_stats['max_create_time']
    if not reviews_count:
      continue

    reviews = list(reviews.order_by('-rating', '-create_time')[:10])
    n = AppStoreReviewNotification(app=app, user=sub.user)
    n.reviews_count = reviews_count

    if sub.email or sub.my_email:
      created_user = None
      if sub.my_email:
        email = sub.user.email
      else:
        created_user = sub.user
        email = sub.email

      unsub_url = unsubscribe_url_for_subscription(sub)
      email_messages.append(
          emails.create_review_email(email, app, reviews_count, reviews, unsub_url,
              created_user=created_user))

      n.email = email
      if sub.my_email:
        n.my_email = True

    elif sub.slack_channel_name or sub.slack_url:
      slack_json = slack_review_json(app, reviews_count, reviews)
      slack.post_message_to_slack_subscription(sub, slack_json)

      if sub.slack_url:
        n.slack_webhook = True
      else:
        n.slack_channel_name = sub.slack_channel_name

    elif sub.twitter_connection:
      # For now, just pick first one for auto-tweeting.
      tweet_review_for_user.delay(sub.user_id, sub.twitter_connection.handle, reviews[0].id)

      n.twitter_handle = sub.twitter_connection.handle

    else:
      continue
      logging.error('WTF? unknown sub: %s', sub.id)

    # NOTE: This is not now() because now() might be different from max(create_time) of this batch,
    # and we use create_time as the filter for the next notification time.
    sub.last_notification_time = reviews_max_create_time
    sub.save(update_fields=['last_notification_time'])
    notifications.append(n)

  if email_messages:
    emails.send_all(email_messages)

  if notifications:
    AppStoreReviewNotification.objects.bulk_create(notifications)


#
# SLACK
#


def slack_enabled_json(apps, user_name):
  if apps:
    app_names = [a.short_name for a in apps]
    app_names_text = '_%s_' % text.english_join(app_names)
    example_app_itunes_url = apps[0].itunes_url
    example_app_icon_small = apps[0].icon_60
  else:
    app_names_text = 'your subscribed apps'
    example_app_itunes_url = settings.SITE_URL
    example_app_icon_small = static('images/icon_app_store.png')

  return {
    'text': (
      "*Review Monitor has been activated by %s and when new reviews for %s are found, "
      "they will be posted to this channel.* "
      "Below is an example of what they will look like."
    ) % (slack.escape(user_name), slack.escape(app_names_text)),
    'icon_url': static('images/reviews/icon.png'),
    'username': 'Review Monitor',
    'attachments': [
      {
        'fallback': 'Example review body',
        'pretext': u'\u0020',
        'title': 'Review Title',
        'text': "Review will be here. Since this is a good review, the bar to the left is green. "
                "If it were 1-2 stars it would be red, and if it were 3 stars it'd be yellow.",
        'color': 'good',
        'mrkdwn_in': ['fields'],
        'author_name': u'★★★★☆',
        'author_link': example_app_itunes_url,
        'author_icon': example_app_icon_small,
        'fields': [
          {
            'value': u'_by AppStoreUser_',
          },
        ],
      }
    ],
  }


def slack_new_apps_added_json(apps):
  attachments = []
  for app in apps:
    attachments.append({
      'fallback': 'App added',
      'author_icon': app.icon_60,
      'author_name': slack.escape(app.short_name),
      'author_link': app.itunes_url,
    })

  return {
    'username': 'Review Monitor',
    'icon_url': static('images/reviews/icon.png'),
    'text': "The following apps have been added to Review Monitor. "
            "Now when new reviews are found, they will be posted to this channel.",
    'attachments': attachments,
  }


def slack_review_json(app, reviews_count, reviews):
  if reviews_count == 1:
    title = '%s has a new App Store review!' % (app.short_name)
  else:
    title = '%s has %s new App Store reviews!' % (app.short_name, reviews_count)

  attachments = []
  for r in reviews:
    review_color = 'good'
    if r.rating < 4:
      review_color = 'warning'
    if r.rating < 3:
      review_color = 'danger'

    attachments.append({
      'title': slack.escape(r.title),
      'title_link': r.public_url,
      'text': slack.escape(r.body),
      'fallback': '*%s*: %s' % (slack.escape(r.title), slack.escape(r.body)),
      'color': review_color,
      'author_name': u'%s%s' % (r.rating_stars, r.rating_empty_stars),
      'author_icon': app.icon_60,
      'mrkdwn_in': ['fields', 'fallback'],
      'fields': [
        {
          'value': u'_by <%s|%s> for v%s_ · %s · <%s|Permalink> · <%s|Tweet>' % (r.author_url, slack.escape(r.author_title), r.app_version, r.country_name, r.public_url, r.tweet_url),
        },
      ],
      'fallback': slack.escape(r.title),
    })

  return {
    'username': 'Review Monitor',
    'icon_url': static('images/icon_app_store.png'),
    'text': title,
    'attachments': attachments,
  }


def _slack_sub_for_user(user):
  subs = AppStoreReviewSubscription.objects.filter(enabled=True, user=user)

  slack_sub = None
  for sub in subs:
    if sub.slack_channel_name:
      slack_sub = sub
      break

  return slack_sub


def debug_send_some_reviews_to_user(user):
  import random
  start = random.randint(0, 100)
  reviews = AppStoreReview.objects.all()[start:start + random.randint(1, 5)]
  message_dict = slack_review_json(reviews[0].app, len(reviews), reviews)

  slack_sub = _slack_sub_for_user(user)
  if not slack_sub:
    logging.info('No slack subs for this user.')
    return

  slack.post_message_to_slack_subscription(slack_sub, message_dict, force=True)


def debug_send_channel_configured_for_user(user):
  import random
  start = random.randint(0, 100)
  apps = AppStoreApp.objects.all()[start:start + random.randint(1, 5)]

  slack_sub = _slack_sub_for_user(user)
  if not slack_sub:
    logging.info('No slack subs for this user.')
    return

  send_slack_subscription_configured_message(slack_sub, apps, force=True)


#
# NEW CONFIGURATIONS
#


def send_slack_subscription_configured_message(sub, apps, force=False):
  slack_json = slack_enabled_json(apps, sub.user.full_name)
  slack.post_message_to_slack_subscription(sub, slack_json, force=force)


def maybe_notify_subs_apps_added(user, apps, force=False):
  slack_subs = []
  email_subs = []
  for sub in AppStoreReviewSubscription.objects.filter(user=user, enabled=True):
    if sub.slack_channel_name or sub.slack_url:
      slack_subs.append(sub)
    elif sub.email:
      # Note: These are not "my email" subs -- these are only emails to people
      # who are not the user who set it up. They will get a "reviews ready"
      # email in a little bit.
      email_subs.append(sub)

  if slack_subs:
    slack_json = slack_new_apps_added_json(apps)
    for sub in slack_subs:
      slack.post_message_to_slack_subscription(sub, slack_json, force=force)

  if email_subs:
    for sub in email_subs:
      send_new_subscription_email(sub, apps)


def send_new_subscription_email(sub, apps):
  unsubscribe_url = unsubscribe_url_for_subscription(sub)
  message = emails.create_reviews_subscription_email(sub.user, sub.email, apps, unsubscribe_url)
  emails.send_all([message])


#
# ACTUALLY SEND MESSAGES
#


@celery_app.task(ignore_result=True)
def tweet_review_for_user(user_id, twitter_handle, review_id, force=False):
  if not (force or settings.IS_PRODUCTION):
    logging.info('Not tweeting review %s on handle @%s for user %s', review_id, twitter_handle, user_id)
    return

  user = User.objects.get(pk=user_id)
  review = AppStoreReview.objects.get(pk=review_id)
  twitter.tweet_review(user, twitter_handle, review)


#
# Notification unsubscribe URLs.
#


def unsubscribe_url_for_subscription(sub):
  base_url = '%sreviews/unsubscribe/' % settings.SITE_URL
  token = crypto_hack.encrypt_object(
      {'time': time.time(), 'sub_id': sub.encrypted_id,},
      settings.UNSUB_SUB_NOTIFY_SECRET)
  return urlutil.appendparams(base_url, token=token)

def subscription_from_unsubscribe_token(token):
  decrypted = crypto_hack.decrypt_object(token, settings.UNSUB_SUB_NOTIFY_SECRET)
  if not decrypted:
    return None
  if decrypted.get('time') < time.time() - (60 * 60 * 24 * 90):
    return None
  return AppStoreReviewSubscription.find_by_encrypted_id(decrypted.get('sub_id'))

