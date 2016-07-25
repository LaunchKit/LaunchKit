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

from django.conf import settings
from django.core.cache import cache
from django.db import connection
from django.db import transaction
from django.db.models import F
from django.db.models import Q

from backend.lk.models import SDKSessionActivity
from backend.lk.models import SDKSession
from backend.lk.models import SDKScreen
from backend.lk.models import SDKTap
from backend.lk.models import SDKUser
from backend.lk.models import SDKUserIncrementLog
from backend.lk.models import SDKVisit
from backend.lk.logic import redis_wrap
from backend.lk.logic import sdk_apps
from backend.lk.logic import session_user_labels
from backend.util import bitwise
from backend.util import text
from backend import celery_app



def get_session_by_encrypted_id(user, encrypted_id):
  decrypted_id = SDKSession.decrypt_id(encrypted_id)
  if not decrypted_id:
    return None

  session = SDKSession.objects.select_for_update().filter(id=decrypted_id).first()
  if session and session.sdk_user_id:
    # Make sure this is fetched for update, since we will almost definitely modify it.
    session.sdk_user = SDKUser.objects.select_for_update().get(pk=session.sdk_user_id)

  return session


def create_session(user, bundle_id):
  sdk_app = sdk_apps.create_or_fetch_sdk_app_with_bundle_id(user, bundle_id)

  sdk_user = SDKUser(user=user, app=sdk_app)
  sdk_user.save()

  session = SDKSession(user=user, app=sdk_app, sdk_user=sdk_user)
  session.save()

  return session


def update_attributes(session, remote_addr,
    version=None, build=None, debug=False,
    screen_width=None, screen_height=None, screen_scale=None,
    os=None, os_version=None, hardware=None,
    sdk_platform=None, sdk_version=None):

  attrs = (
    ('app_version', version),
    ('app_build', build),
    ('app_build_debug', debug),
    ('os', os),
    ('os_version', os_version),
    ('hardware', hardware),
    ('screen_width', screen_width),
    ('screen_height', screen_height),
    ('screen_scale', screen_scale),
    ('sdk_platform', sdk_platform),
    ('sdk_version', sdk_version),
  )

  modified = {}
  for k, v in attrs:
    existing_v = getattr(session, k, None)
    if existing_v != v:
      setattr(session, k, v)
      modified[k] = (existing_v, v)

  if modified:
    upgraded = False
    if 'app_version' in modified:
      previous_version, next_version = modified['app_version']
      if previous_version and next_version:
        upgraded = text.cmp_version(next_version, previous_version) > 0
    if not upgraded and 'app_build' in modified:
      previous_build, next_build = modified['app_build']
      if previous_build and next_build:
        upgraded = text.cmp_build(next_build, previous_build) > 0

    if upgraded:
      session.last_upgrade_time = datetime.now()

    session.save()

    a = SDKSessionActivity(user=session.user, session=session, kind='updated-session')
    a.remote_addr = remote_addr
    a.data['changed'] = ','.join(modified.keys())
    for k, (v1, v2) in modified.items():
      if v1 is not None:
        a.data['%s_before' % k] = '%s' % v1
      a.data['%s_after' % k] = '%s' % v2

    a.save()


@transaction.atomic
def set_user_info(session, remote_addr, unique_id=None, email=None, name=None):
  # null out values
  unique_id = unique_id or None
  email = email or None
  name = name or None

  user_attrs = ('unique_id', 'email', 'name')
  before_attrs = {k: getattr(session.sdk_user, k, None) for k in user_attrs}
  _set_user_info_no_log(session, unique_id=unique_id, email=email, name=name)
  after_attrs = {k: getattr(session.sdk_user, k, None) for k in user_attrs}

  changed_attrs = {}
  for k in before_attrs:
    if after_attrs[k] != before_attrs[k]:
      changed_attrs['before_%s' % k] = before_attrs[k]
      changed_attrs['after_%s' % k] = after_attrs[k]

  if changed_attrs:
    a = SDKSessionActivity(user=session.user, session=session, kind='updated-user')
    a.remote_addr = remote_addr
    a.data = changed_attrs
    a.save()


def _set_user_info_no_log(session, unique_id=None, email=None, name=None):
  existing = session.sdk_user
  switching_to_anonymous = not (unique_id or email or name)

  # FROM ANY USER TO ANONYMOUS USER

  if switching_to_anonymous:
    # Setting to anonymous session; just make sure we're also anonymous.
    if not (existing and existing.is_anonymous()):
      # set anonymous user
      anonymous_user = SDKUser(user_id=session.user_id, app_id=session.app_id)
      anonymous_user.save()
      session.sdk_user = anonymous_user
      session.save()
    return

  # FROM ANONYMOUS USER TO NON-ANONYMOUS USER

  matching = None
  if unique_id:
    matching = (
      SDKUser.objects
        .filter(user_id=session.user_id, app_id=session.app_id, unique_id=unique_id)
        .select_for_update()
        .first()
    )

  if existing and existing.is_anonymous():
    if not matching:
      # Take over anonymous session.
      existing.unique_id = unique_id
      existing.email = email
      existing.name = name
      existing.save()
      return

    # Transfer stats from existing anonymous user to new matching user.
    session.sdk_user = matching
    SDKUser.objects.filter(id=matching.id).update(
      name=name,
      email=email,

      visits=F('visits') + existing.visits,
      screens=F('screens') + existing.screens,
      taps=F('taps') + existing.taps,
      seconds=F('seconds') + existing.seconds,

      monthly_visits=F('monthly_visits') + existing.monthly_visits,
      monthly_screens=F('monthly_screens') + existing.monthly_screens,
      monthly_taps=F('monthly_taps') + existing.monthly_taps,
      monthly_seconds=F('monthly_seconds') + existing.monthly_seconds,
    )
    # Transfer decrementing counts to new object to cancel out these numbers.
    SDKUserIncrementLog.objects.filter(sdk_user_id=existing.id).update(sdk_user_id=matching.id)

    existing.visits = 0
    existing.screens = 0
    existing.taps = 0
    existing.seconds = 0
    existing.monthly_visits = 0
    existing.monthly_screens = 0
    existing.monthly_taps = 0
    existing.monthly_seconds = 0
    existing.save()
    session.save()

    session_user_labels.mark_sdk_user_labels_dirty([existing.id, matching.id])
    return

  if matching:
    # Switch users to an existing user.
    if matching.email != email or matching.name != name:
      matching.email = email
      matching.name = name
      matching.save()
    session.sdk_user = matching
    session.save()
    return

  # Switch users to a new user.
  new_user = SDKUser(user_id=session.user_id, app_id=session.app_id, unique_id=unique_id, email=email, name=name)
  new_user.save()
  session.sdk_user = new_user
  session.save()


VISIT_BOUNDARY = timedelta(minutes=5)
COPY_SESSION_ATTRS_TO_VISIT = (
    'sdk_user', 'os', 'os_version', 'hardware', 'app_version',
    'app_build', 'app_build_debug', 'screen_height',
    'screen_width', 'screen_scale',
)

def _visits_for_ranges(session, raw_ranges):
  if not raw_ranges:
    return (), ()

  reduced_ranges = []
  current_range = None
  for start, end in sorted(raw_ranges):
    if not current_range or current_range[1] + VISIT_BOUNDARY < end:
      current_range = [start, end]
      reduced_ranges.append(current_range)

    else:
      # these are sorted by the start time, so it is possible
      # to get an end time here that is earlier than a previous
      # end time
      current_range[1] = max(end, current_range[1])

  latest_visit_by_session_key = 'sdkvisit-by-session:%d' % session.id
  latest_visit_cached = cache.get(latest_visit_by_session_key)
  new_latest_visit = None

  new_visits = []
  existing_visits = []
  for i, (start, end) in enumerate(reduced_ranges):
    end_boundary = end + VISIT_BOUNDARY
    start_boundary = start - VISIT_BOUNDARY

    if (latest_visit_cached and
        latest_visit_cached.start_time <= end_boundary and
        latest_visit_cached.end_time >= start_boundary):
      visit = latest_visit_cached
      latest_visit_cached = None

    else:
      # http://stackoverflow.com/questions/325933 -- excellent.
      visit = SDKVisit.objects.filter(session_id=session.id,
          start_time__lte=end_boundary,
          end_time__gte=start_boundary).first()

    if visit:
      visit.start_time = min(start, visit.start_time)
      visit.end_time = max(end, visit.end_time)
      visit.save(update_fields=['start_time', 'end_time'])
      existing_visits.append(visit)

    else:
      visit = SDKVisit(user_id=session.user_id, session=session,
                       start_time=start, end_time=end,
                       screens=0, taps=0)
      for k in COPY_SESSION_ATTRS_TO_VISIT:
        setattr(visit, k, getattr(session, k))
      new_visits.append(visit)

    new_latest_visit = visit

  for v in new_visits:
    v.save()

  if new_latest_visit:
    cache.set(latest_visit_by_session_key, new_latest_visit, 60 * 30)

  return new_visits, existing_visits


def track_event(session, event_name, remote_addr, **track_data):
  evt = SDKSessionActivity(user=session.user, session=session, kind=event_name)
  evt.remote_addr = remote_addr
  if track_data:
    for k, v in track_data.items():
      evt.data[k] = '%s' % v
  evt.save()


def track(session, event_name, raw_taps=None, raw_screens=None):
  taps = [SDKTap(time=t.time, x=t.x, y=t.y, orient=t.orient)
          for t in raw_taps or []]
  screens = [SDKScreen(start_time=s.start, end_time=s.end, name=s.name)
             for s in raw_screens or []]

  new_visits, existing_visits = _visits_for_ranges(session,
      [(s.start_time, s.end_time) for s in screens] + [(t.time, t.time) for t in taps])
  session_visits = sorted(new_visits + existing_visits, key=lambda v: v.start_time)

  for screen in screens:
    matching_visit = None
    for visit in session_visits:
      if visit.start_time <= screen.start_time and visit.end_time >= screen.end_time:
        matching_visit = visit
        break

    screen.visit = matching_visit
    matching_visit.screens += 1

  for tap in taps:
    matching_visit = None
    for visit in session_visits:
      if visit.start_time <= tap.time and visit.end_time >= tap.time:
        matching_visit = visit
        break

    tap.visit = matching_visit
    matching_visit.taps += 1

  for visit in session_visits:
    visit.save(update_fields=['screens', 'taps'])

  updates_by_date = collections.defaultdict(lambda: collections.defaultdict(lambda: 0))

  tap_count = len(taps)
  for tap in taps:
    updates_by_date[tap.time.date()]['monthly_taps'] += 1

  seconds_count = 0
  screens_count = len(screens)
  for screen in screens:
    this_screen_seconds = (s.end_time - s.start_time).total_seconds()
    seconds_count += this_screen_seconds
    screen_update = updates_by_date[screen.start_time.date()]
    screen_update['monthly_screens'] += 1
    screen_update['monthly_seconds'] += this_screen_seconds

  new_visits_count = len(new_visits)
  for visit in new_visits:
    updates_by_date[visit.start_time.date()]['monthly_visits'] += 1

  SDKSession.objects.filter(id=session.id).update(
    last_accessed_time=datetime.now(),
    taps=F('taps') + tap_count,
    screens=F('screens') + screens_count,
    visits=F('visits') + new_visits_count,
    seconds=F('seconds') + seconds_count,
  )

  if not session.sdk_user_id:
    return

  #
  # UPDATE USER
  #

  sdk_user = session.sdk_user

  dates_visited = set(s.start_time.date() for s in screens)
  dates_visited.update(t.time.date() for t in taps)

  relative_active_bitmask = 0
  for d in dates_visited:
    days_offset = sdk_user.days_active_bitmap_offset_for_date(now_date=d)
    day_bit = 1 << days_offset
    relative_active_bitmask |= day_bit

  # Find this here so we can update the row with number of active days.
  valid_days_bitmask = session.sdk_user.days_active_bitmap_valid_bitmask()
  days_active_map = (sdk_user.days_active_map | relative_active_bitmask) & valid_days_bitmask
  days_active = bitwise.num_bits_64(days_active_map)

  if sdk_user.days_active_map != days_active_map:
    # Update these here for subsequent labels update
    sdk_user.days_active_map = days_active_map
    sdk_user.monthly_days_active = days_active
    sdk_user.monthly_visits += new_visits_count
    sdk_user.monthly_seconds += seconds_count

  SDKUser.objects.filter(id=sdk_user.id).update(
    last_accessed_time=datetime.now(),
    taps=F('taps') + tap_count,
    screens=F('screens') + screens_count,
    visits=F('visits') + new_visits_count,
    seconds=F('seconds') + seconds_count,

    monthly_taps=F('monthly_taps') + tap_count,
    monthly_screens=F('monthly_screens') + screens_count,
    monthly_visits=F('monthly_visits') + new_visits_count,
    monthly_seconds=F('monthly_seconds') + seconds_count,

    days_active_map=(
        F('days_active_map')
          .bitor(bitwise.to_psql_int64(relative_active_bitmask))
          .bitand(bitwise.to_psql_int64(valid_days_bitmask))
    ),
    monthly_days_active=days_active,
  )

  logs_by_day = []
  for date, updates in updates_by_date.items():
    date = date + timedelta(days=1)
    # Use the current time, but on the relevant date, so we can
    # distribute edits throughout the day and approximate create time.
    now = datetime.now()
    create_time = datetime(date.year, date.month, date.day,
        now.hour, now.minute, now.second, now.microsecond)

    log = SDKUserIncrementLog(
        sdk_user_id=sdk_user.id,
        create_time=create_time,
        data=dict((k, '%s' % v) for k, v in updates.items()))
    logs_by_day.append(log)

  if logs_by_day:
    SDKUserIncrementLog.objects.bulk_create(logs_by_day)

  # Finally, maybe update labels on the user.
  session_user_labels.update_labels_for_user(sdk_user)


#
# TOP USERS
#


TOP_USER_SORTABLE_ATTRIBUTES = [k for k in dir(SDKUser()) if k.startswith('monthly_')] + ['last_accessed_time']

def top_users(user, app, sort_key, query=None, start_sdk_user=None, limit=100):
  users = SDKUser.objects.filter(user=user, app=app)
  users = users.order_by('-%s' % sort_key, 'id')

  if start_sdk_user:
    lt_kwargs = {'%s__lt' % sort_key: getattr(start_sdk_user, sort_key)}
    lte_kwargs = {sort_key: getattr(start_sdk_user, sort_key), 'id__gt': start_sdk_user.id}
    users = users.filter(Q(**lt_kwargs) | Q(**lte_kwargs))

  if query:
    qs_parts = Q(unique_id=query) | Q(email__icontains=query)
    name_part = None
    for part in query.split():
      if not part:
        continue
      my_part = Q(name__icontains=part)
      if not name_part:
        name_part = my_part
      else:
        name_part &= my_part
    if name_part:
      qs_parts |= name_part

    users = users.filter(qs_parts)

  return users[:limit]


#
# DAYS VISITED BY USER
#


def days_active_for_user(sdk_user, days=180):
  cursor = connection.cursor()
  cursor.execute("""
    SELECT start_time::DATE AS start_date, COUNT(*)
    FROM lk_sdkvisit
    WHERE sdk_user_id=%s AND start_time > NOW() - INTERVAL %s
    GROUP BY start_date ORDER BY start_date DESC
  """, [sdk_user.id, '%s days' % days])

  days_active = []
  for start_date, count in cursor.fetchall():
    timestamp = time.mktime(start_date.timetuple())
    days_active.append((timestamp, count))
  return days_active



#
# BACKGROUND TASKS FOR SESSION MAINTENANCE
#


@celery_app.task(ignore_result=True, queue='sessions')
def process_session_data():
  process_sdkuser_days_active()
  process_sdkuser_increment_log()


#
# UPDATE SDKUSER ACTIVE DAYS COUNTS
#


PROCESS_SDKUSERS_LIMIT = 100

@transaction.atomic
def process_sdkuser_days_active_from_id(max_id, future_days_offset=0):
  if settings.IS_PRODUCTION and future_days_offset:
    raise RuntimeError('Not to be used in production')

  users = list(
      SDKUser.objects
        .select_for_update()
        .filter(id__gt=max_id)
        .order_by('id')[:PROCESS_SDKUSERS_LIMIT])

  update_infos = []
  updated_user_ids = []
  for sdk_user in users:
    days_active_map = sdk_user.days_active_map & sdk_user.days_active_bitmap_valid_bitmask(now_days_offset=future_days_offset)
    psql_days_active_map = bitwise.to_psql_int64(days_active_map)
    days_active = bitwise.num_bits_64(days_active_map)

    if (psql_days_active_map != sdk_user.days_active_map or days_active != sdk_user.monthly_days_active):
      SDKUser.objects.filter(id=sdk_user.id).update(
          days_active_map=psql_days_active_map,
          monthly_days_active=days_active
      )
      update_infos.append((sdk_user.monthly_days_active, days_active))
      updated_user_ids.append(sdk_user.id)

  if updated_user_ids:
    logging.info('Updated %s sdkusers... %s',
        len(updated_user_ids), ' '.join(['%d->%d' % (b, a) for b, a in update_infos[:5]]))
    session_user_labels.mark_sdk_user_labels_dirty(updated_user_ids)

  if len(users) < PROCESS_SDKUSERS_LIMIT:
    logging.info('Starting over at the beginning of SDK users table...')
    return -1

  return users[-1].id


LAST_SDKUSER_PROCESSED_KEY = 'sessions:max-sdkuser-id'

def process_sdkuser_days_active():
  redis = redis_wrap.client()
  max_id = redis.get(LAST_SDKUSER_PROCESSED_KEY) or 0

  new_max_id = process_sdkuser_days_active_from_id(max_id)

  if new_max_id:
    logging.info('New max id: %s', new_max_id)
    redis.set(LAST_SDKUSER_PROCESSED_KEY, new_max_id)


#
# WORK THROUGH SDKUSER INCREMENT LOG
#


INCREMENT_LOG_BATCH_SIZE = 250

@transaction.atomic
def process_sdkuser_increment_log(future_days_offset=0):
  if settings.IS_PRODUCTION and future_days_offset:
    raise RuntimeError('Not to be used in production')

  threshold = datetime.now() - timedelta(days=(30 - future_days_offset))
  raw_changes = list(
      SDKUserIncrementLog.objects
        .filter(create_time__lt=threshold)
        .select_for_update()
        .order_by('create_time', 'id')[:INCREMENT_LOG_BATCH_SIZE]
    )
  if not raw_changes:
    return

  max_create_time = raw_changes[-1].create_time
  max_id = raw_changes[-1].id
  create_time_lt = Q(create_time__lt=max_create_time)
  create_time_eq_id_lte = Q(create_time=max_create_time, id__lte=max_id)
  SDKUserIncrementLog.objects.filter(create_time_lt | create_time_eq_id_lte).delete()

  changed_user_ids = []
  changes = []
  for change in raw_changes:
    if not (change.data and any(v for k, v in change.data.iteritems())):
      continue
    changes.append(change)
    changed_user_ids.append(change.sdk_user_id)

  # Just select these in order to lock them upfront, otherwise another
  # transaction might lock them in a different order and cause deadlock.
  list(SDKUser.objects.filter(id__in=changed_user_ids).select_for_update().values_list('id'))

  cursor = connection.cursor()
  # IMPORTANT: Sort here by user ID so updates to user rows happen in the same order
  # across various transactions.
  for change in sorted(changes, key=lambda c: (c.sdk_user_id, c.id)):
    updates = ['%s = GREATEST(%s - %s, 0)' % (field, field, incr) for field, incr in change.data.items()]
    cursor.execute("""
      UPDATE lk_sdkuser SET %s WHERE id = %%s
    """ % ','.join(updates), [change.sdk_user_id])

  if changed_user_ids:
    logging.info('Increment log decremented %s rows...', len(changed_user_ids))
    session_user_labels.mark_sdk_user_labels_dirty(changed_user_ids)
