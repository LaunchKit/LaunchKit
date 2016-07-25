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

import collections
import logging
import time
from datetime import datetime
from datetime import timedelta

from django.db import transaction
from redis import WatchError

from backend.lk.logic import redis_wrap
from backend.lk.models import ActiveStatus
from backend.lk.models import CumulativeTimeUsed
from backend.lk.models import SessionFrequency
from backend.lk.models import DEFAULT_SUPER_CONFIG_FREQ
from backend.lk.models import DEFAULT_SUPER_CONFIG_TIME
from backend.lk.models import DEFAULT_ALMOST_CONFIG_FREQ
from backend.lk.models import DEFAULT_ALMOST_CONFIG_TIME
from backend.lk.models import CUMULATIVE_TIME_ORDER
from backend.lk.models import SESSION_FREQUENCY_ORDER
from backend.lk.models import SDKApp
from backend.lk.models import SDKAppStat
from backend.lk.models import SDKUser
from backend.lk.models import SDKUserLabelChangeEvent
from backend import celery_app


TRACK_LABEL_COMBINATIONS = []
for freq in SessionFrequency.kinds():
  for time_used in CumulativeTimeUsed.kinds():
    TRACK_LABEL_COMBINATIONS.append((freq, time_used))


def super_labels_for_app(app):
  if app.super_config:
    return set(app.super_config)
  return set([DEFAULT_SUPER_CONFIG_FREQ, DEFAULT_SUPER_CONFIG_TIME])


def almost_labels_for_app(app):
  if app.almost_config:
    return set(c for c in app.almost_config if c)
  return set([DEFAULT_ALMOST_CONFIG_FREQ, DEFAULT_ALMOST_CONFIG_TIME])


def set_super_config(app, super_freq, super_time):
  # Determine "almost" config based on next values behind super values.
  freqs = SESSION_FREQUENCY_ORDER
  next_idx = freqs.index(super_freq) + 1
  if next_idx < len(freqs):
    almost_freq = freqs[next_idx]
  else:
    almost_freq = None

  times = CUMULATIVE_TIME_ORDER
  next_idx = times.index(super_time) + 1
  if next_idx < len(times):
    almost_time = times[next_idx]
  else:
    almost_time = None

  app.super_config = [super_freq, super_time]
  app.almost_config = [almost_freq, almost_time]
  app.save(update_fields=['super_config', 'almost_config'])


def labels_for_user(user, future_days_offset=0):
  labels = set()

  weekly_days_active = user.weekly_days_active(now_days_offset=future_days_offset)
  monthly_days_active = user.monthly_days_active
  monthly_visits = user.monthly_visits
  monthly_seconds = user.monthly_seconds

  if monthly_days_active > 0:
    labels.add(ActiveStatus.MonthlyActive)
  else:
    labels.add(ActiveStatus.MonthlyInactive)

  if weekly_days_active >= 1:
    labels.add(ActiveStatus.WeeklyActive)
  else:
    labels.add(ActiveStatus.WeeklyInactive)

  if weekly_days_active == 7 or monthly_days_active >= 28:
    if monthly_visits > (29 * 3):
      labels.add(SessionFrequency.MoreThanOnceADay)
    labels.add(SessionFrequency.OnceADay)

  if weekly_days_active >= 5 or monthly_days_active >= 20:
    labels.add(SessionFrequency.FiveDaysAWeek)

  if weekly_days_active >= 3 or monthly_days_active >= 12:
    labels.add(SessionFrequency.ThreeDaysAWeek)

  if weekly_days_active >= 1 or monthly_days_active >= 4:
    labels.add(SessionFrequency.OnceAWeek)

  if monthly_days_active >= 2:
    labels.add(SessionFrequency.TwiceAMonth)

  seconds_per_day = float(monthly_seconds) / max(monthly_days_active, 1)
  if seconds_per_day > (60 * 60):
    labels.add(CumulativeTimeUsed.HourPerDay)

  if seconds_per_day > (60 * 15):
    labels.add(CumulativeTimeUsed.FifteenMinutesPerDay)
  if seconds_per_day > (60 * 5):
    labels.add(CumulativeTimeUsed.FiveMinutesPerDay)
  if seconds_per_day > 60:
    labels.add(CumulativeTimeUsed.OneMinutePerDay)
  if seconds_per_day > 30:
    labels.add(CumulativeTimeUsed.ThirtySecondsPerDay)

  existing_labels = set(user.labels or [])
  super_labels = super_labels_for_app(user.app)
  almost_labels = almost_labels_for_app(user.app)

  if super_labels & labels == super_labels:
    labels.add('super')
  elif almost_labels & labels == almost_labels:
    newly_fringe = 'super' in existing_labels
    already_fringe = 'fringe' in existing_labels
    if newly_fringe or already_fringe:
      # Fringe is a super user who lost super status and is in the next
      # category down -- almost. But almost and fringe are mutually
      # exclusive.
      labels.add('fringe')

    # always add almost
    labels.add('almost')

  return labels



CURRENT_COUNT_REDIS_KEY_FORMAT = 'sessions;label-counts;app-id=%s'


@transaction.atomic
def update_labels_for_user(sdk_user, future_days_offset=0):
  old_labels = set(sdk_user.labels or [])
  new_labels = labels_for_user(sdk_user, future_days_offset=future_days_offset)

  if old_labels == new_labels:
    return False

  change_events = []
  increment_label_by = collections.defaultdict(lambda: 0)

  removed_labels = old_labels - new_labels
  for label in removed_labels:
    change_event = SDKUserLabelChangeEvent(app_id=sdk_user.app_id, sdk_user_id=sdk_user.id, user_id=sdk_user.user_id,
                                           label=label, kind='removed')
    increment_label_by[label] -= 1
    change_events.append(change_event)

  added_labels = new_labels - old_labels
  for label in added_labels:
    change_event = SDKUserLabelChangeEvent(app_id=sdk_user.app_id, sdk_user_id=sdk_user.id, user_id=sdk_user.user_id,
                                           label=label, kind='added')
    increment_label_by[label] += 1
    change_events.append(change_event)

  # Create change events and update labels on user.

  SDKUserLabelChangeEvent.objects.bulk_create(change_events)

  labels = list(sorted(new_labels))
  sdk_user.labels = labels
  sdk_user.save(update_fields=['labels'])

  # Now track the changes we've made in our counts.

  for l1, l2 in TRACK_LABEL_COMBINATIONS:
    had_label = l1 in old_labels and l2 in old_labels
    has_label = l1 in new_labels and l2 in new_labels

    if had_label != has_label:
      if had_label:
        # removed label
        increment = -1
      else:
        # added label
        increment = 1

      combined_label = '%s-%s' % (l1, l2)
      increment_label_by[combined_label] = increment

  redis = redis_wrap.client()
  redis_key = CURRENT_COUNT_REDIS_KEY_FORMAT % sdk_user.app_id

  with redis.pipeline() as pipe:
    for label, increment in increment_label_by.items():
      pipe.hincrby(redis_key, label, increment)
    pipe.execute()

  # logging.info('Updated sdk user %s labels: %s', sdk_user.id, labels)

  return True


def label_counts_by_app_ids(app_ids):
  redis = redis_wrap.client()

  results = None
  with redis.pipeline() as pipe:
    for app_id in app_ids:
      redis_key = CURRENT_COUNT_REDIS_KEY_FORMAT % app_id
      pipe.hgetall(redis_key)

    results = pipe.execute()

  response = {}
  for app_id, result in zip(app_ids, results):
    response[app_id] = {k: int(v) for k, v in result.items()}
  return response


def label_counts_for_app_id(app_id):
  return label_counts_by_app_ids([app_id])[app_id]


DIRTY_SDK_USER_LABELS_REDIS_KEY = 'sessions;dirty-sdk-users'

def mark_sdk_user_labels_dirty(sdk_user_ids):
  if not sdk_user_ids:
    return

  t = time.time()
  rescored_user_ids = []

  user_ids_uniq = set(sdk_user_ids)
  for user_id in user_ids_uniq:
    rescored_user_ids.append(t)
    rescored_user_ids.append(user_id)

  redis = redis_wrap.client()
  redis.zadd(DIRTY_SDK_USER_LABELS_REDIS_KEY, *rescored_user_ids)


@celery_app.task(ignore_result=True, queue='sessions')
def process_dirty_sdk_user_labels():
  now_timestamp = time.time()

  sdk_user_ids_needing_attention = []

  # Atomically find next app ids to check.
  redis = redis_wrap.client()
  while True:
    with redis.pipeline() as pipe:
      try:
        pipe.watch(DIRTY_SDK_USER_LABELS_REDIS_KEY)
        sdk_user_ids_needing_attention = pipe.zrangebyscore(DIRTY_SDK_USER_LABELS_REDIS_KEY,
            0, now_timestamp,
            start=0, num=50)

        if sdk_user_ids_needing_attention:
          pipe.multi()
          pipe.zrem(DIRTY_SDK_USER_LABELS_REDIS_KEY, *sdk_user_ids_needing_attention)
          pipe.execute()

        break
      except WatchError:
        logging.info('Interrupted while fetching app ids to ingest...')

  updates = 0
  with transaction.atomic():
    # Select these in a single transaction instead of individually to avoid lock contention.
    sdk_users_needing_attention = list(
        SDKUser.objects
          .filter(id__in=sdk_user_ids_needing_attention)
          .select_for_update()
          .order_by('id')
    )
    for sdk_user in sdk_users_needing_attention:
      if update_labels_for_user(sdk_user):
        updates += 1

  if updates:
    logging.info('Updated %s sdk user rows labels...', updates)


@celery_app.task(ignore_result=True, queue='sessions')
def process_weekly_inactive_sessions(future_days_offset=0):
  updates = 0

  with transaction.atomic():
    week_ago_days = 7 - future_days_offset
    one_week_ago = datetime.now() - timedelta(days=week_ago_days, hours=1)
    old_users = list(
      SDKUser.objects
        .select_for_update()
        .filter(last_accessed_time__lt=one_week_ago)
        .extra(where=['labels @> ARRAY[%s]'], params=[ActiveStatus.WeeklyActive])
        .order_by('id')[:250]
    )

    for user in old_users:
      if update_labels_for_user(user, future_days_offset=future_days_offset):
        updates += 1

  if updates:
    logging.info('Updated %s weekly inactive sdk user rows labels...', updates)



PROCESS_SDKUSERS_LABELS_LIMIT = 250
LAST_SDKUSER_LABELS_PROCESSED_KEY = 'sessions:labels:max-sdkuser-id'

@celery_app.task(ignore_result=True, queue='sessions')
def process_sdkuser_labels_periodically():
  redis = redis_wrap.client()
  max_id = redis.get(LAST_SDKUSER_LABELS_PROCESSED_KEY) or 0

  with transaction.atomic():
    sdk_users = list(
      SDKUser.objects
        .select_for_update()
        .filter(id__gt=max_id)
        .order_by('id')[:PROCESS_SDKUSERS_LABELS_LIMIT]
    )

    if sdk_users:
      new_max_id = sdk_users[-1].id
      updates = 0
      for sdk_user in sdk_users:
        if update_labels_for_user(sdk_user):
          updates += 1

      if updates:
        logging.info('Updated %s sdk user labels periodically', updates)

    else:
      logging.info('No more users to update labels, starting over')
      new_max_id = 0

  redis.set(LAST_SDKUSER_LABELS_PROCESSED_KEY, new_max_id)


#
# HOURLY LABEL GRAPHS
#


@celery_app.task(ignore_result=True, queue='sessions')
def save_hourly_label_counts():
  last_id = 0
  while True:
    apps = list(SDKApp.objects.filter(id__gt=last_id).order_by('id')[:50])
    if not apps:
      break

    app_ids = [a.id for a in apps]
    last_id = app_ids[-1]

    counts_by_app_id = label_counts_by_app_ids(app_ids)
    now = datetime.now()
    hour = datetime(now.year, now.month, now.day, now.hour, 0, 0)

    for app in apps:
      counts = {'%s' % k: '%s' % v for k, v in counts_by_app_id.get(app.id, {}).items() if v is not None}
      stat = SDKAppStat(user_id=app.user_id, app_id=app.id, hour=hour, data=counts)
      try:
        stat.save()
      except Exception as e:
        logging.warn('Could not save stat for app id: %s hour: %s (reason: %s)', app.id, hour, e)
