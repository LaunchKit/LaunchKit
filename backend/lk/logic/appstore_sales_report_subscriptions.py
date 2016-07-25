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

from backend.lk.logic import emails
from backend.lk.logic import itunes_connect
from backend.lk.logic import slack
from backend.lk.models import AppStoreSalesReportSubscription
from backend import celery_app


def create_email_subscription(user, email):
  subs = AppStoreSalesReportSubscription.objects.filter(user=user)
  subs = list(subs.extra(where=["data->'email'=%s"], params=[email]))
  if subs:
    sub = subs[0]
  else:
    sub = AppStoreSalesReportSubscription(user=user)
    sub.email = email

  if sub.enabled:
    # Already have this sub.
    return None

  sub.enabled = True
  sub.save()

  itunes_connect.maybe_send_latest_report_to_user(user)

  return sub


def create_my_email_subscription(user):
  subs = AppStoreSalesReportSubscription.objects.filter(user=user)
  subs = list(subs.extra(where=["data->'my_email'='1'"]))
  if subs:
    sub = subs[0]
  else:
    sub = AppStoreSalesReportSubscription(user=user)
    sub.my_email = True

  if sub.enabled:
    # Already have this sub.
    return None

  sub.enabled = True
  sub.save()

  itunes_connect.maybe_send_latest_report_to_user(user)

  return sub


def create_slack_subscription(user, slack_url):
  subs = AppStoreSalesReportSubscription.objects.filter(user=user)
  subs = list(subs.extra(where=["data->'slack_url'=%s"], params=[slack_url]))
  if subs:
    sub = subs[0]
  else:
    sub = AppStoreSalesReportSubscription(user=user)
    sub.slack_url = slack_url

  if sub.enabled:
    # Already have this sub.
    return None

  sub.enabled = True
  sub.save()

  itunes_connect.send_slack_subscription_configured_message(sub)
  itunes_connect.maybe_send_latest_report_to_user(user)

  return sub


def create_slack_channel_subscription(user, slack_channel_name):
  subs = AppStoreSalesReportSubscription.objects.filter(user=user)
  subs = list(subs.extra(where=["data->'slack_channel_name'=%s"], params=[slack_channel_name]))
  if subs:
    sub = subs[0]
  else:
    sub = AppStoreSalesReportSubscription(user=user)
    sub.slack_channel_name = slack_channel_name

  if sub.enabled:
    # Already have this sub.
    return None

  sub.enabled = True
  sub.save()

  itunes_connect.send_slack_subscription_configured_message(sub)
  itunes_connect.maybe_send_latest_report_to_user(user)

  return sub


def subscribed_slack_channel_names(user):
  subs = AppStoreSalesReportSubscription.objects.filter(user=user, enabled=True)
  subs = list(subs.extra(where=["(data->'slack_channel_name')::text IS NOT NULL"]))
  return [sub.slack_channel_name for sub in subs]


def invalidate_slack_channel_subscriptions(user):
  AppStoreSalesReportSubscription.objects \
      .filter(user=user) \
      .extra(where=["(data->'slack_channel_name')::text IS NOT NULL"]) \
      .update(enabled=False)


def get_user_subscription_by_encrypted_id(user, encrypted_sub_id):
  sub = AppStoreSalesReportSubscription.find_by_encrypted_id(encrypted_sub_id)
  if sub and sub.user_id == user.id and sub.enabled:
    return sub
  return None


def disable_subscription(subscription):
  subscription.enabled = False
  subscription.save()


def subscriptions_for_user(user):
  return AppStoreSalesReportSubscription.objects.filter(user=user, enabled=True)
