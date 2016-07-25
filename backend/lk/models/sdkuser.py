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

from datetime import datetime
from datetime import timedelta

from django.db import models
from djorm_pgarray.fields import TextArrayField

from backend.lk.models.apimodel import APIModel
from backend.lk.models.sdkapp import SDKApp
from backend.lk.models.users import User
from backend.util import bitwise
from backend.util import hstore_field


DAYS_IN_MONTH = 30


class SDKUser(APIModel):
  class Meta:
    app_label = 'lk'
    unique_together = ('app', 'unique_id',)

  ENCRYPTED_ID_KEY_TOKEN = 'sdk-user'

  user = models.ForeignKey(User, related_name='+', on_delete=models.DO_NOTHING)
  app = models.ForeignKey(SDKApp, related_name='+', on_delete=models.DO_NOTHING)

  create_time = models.DateTimeField(auto_now_add=True)
  last_accessed_time = models.DateTimeField(auto_now_add=True)

  unique_id = models.CharField(max_length=128, null=True)
  name = models.CharField(max_length=128, null=True)
  email = models.CharField(max_length=128, null=True)

  screens = models.PositiveIntegerField(default=0)
  taps = models.PositiveIntegerField(default=0)
  visits = models.PositiveIntegerField(default=0)
  seconds = models.PositiveIntegerField(default=0)

  days_active_map = models.BigIntegerField(default=0)

  monthly_screens = models.PositiveIntegerField(default=0)
  monthly_taps = models.PositiveIntegerField(default=0)
  monthly_visits = models.PositiveIntegerField(default=0)
  monthly_seconds = models.PositiveIntegerField(default=0)
  monthly_days_active = models.PositiveIntegerField(default=0)

  labels = TextArrayField(null=True)
  data = hstore_field.HStoreField(null=True)

  def is_anonymous(self):
    return not (self.unique_id or self.name or self.email)

  @property
  def monthly_days_active_computed(self):
    return bitwise.num_bits_64(self.last_month_active_bitmap())

  def last_month_active_bitmap(self, now_days_offset=0):
    offset = self.days_active_bitmap_offset_for_date(now_days_offset=now_days_offset)
    # This is DAYS_IN_MONTH - 1 here because today is bit 0.
    shift = offset - (DAYS_IN_MONTH - 1)
    days_active_map = (self.days_active_map or 0) & bitwise.BITS_64
    shifted_map = bitwise.wrapping_right_shift_64(days_active_map, shift)
    return shifted_map & bitwise.flipped_bits_64(DAYS_IN_MONTH)

  def weekly_days_active(self, now_days_offset=0):
    return bitwise.num_bits_64(self.weekly_days_active_bitmap(now_days_offset=now_days_offset))

  def weekly_days_active_bitmap(self, now_days_offset=0):
    return self.last_month_active_bitmap_reversed(now_days_offset=now_days_offset) & 0b1111111

  def last_month_active_bitmap_reversed(self, now_days_offset=0):
    # You will get a DAYS_IN_MONTH-long bitmap, shifted so that:
    # today is (map & 1), yest. is (map & (1 << 1)), 2d ago is (map & (1 << 2))
    return bitwise.reverse_bits(self.last_month_active_bitmap(now_days_offset=now_days_offset), DAYS_IN_MONTH)

  def days_active_bitmap_offset_for_date(self, now_date=None, now_days_offset=0):
    if now_date is None:
      now_date = datetime.now().date()
      if now_days_offset is not None:
        now_date += timedelta(days=now_days_offset)

    return (now_date - self.create_time.date()).days % 64

  def days_active_bitmap_valid_bitmask(self, now_days_offset=0):
    # By default, this is tomorrow's offset.
    offset = self.days_active_bitmap_offset_for_date(now_days_offset=(1 + now_days_offset))
    return bitwise.trailing_window_bitmask_64(offset, DAYS_IN_MONTH)

  @property
  def filtered_labels(self):
    if not self.labels:
      return []

    labels = []
    for label in ['super', 'almost', 'fringe']:
      if label in self.labels:
        labels.append(label)
    if 'active-1m' in self.labels:
      labels.append('active')
    else:
      labels.append('inactive')

    return labels

  def to_client_dict(self):
    return {
      'name': self.name,
      'uniqueId': self.unique_id,
      'email': self.email,

      'firstVisit': self.date_to_api_date(self.create_time),

      'stats': {
        'visits': self.monthly_visits,
        'days': self.monthly_days_active_computed,
      },

      'labels': self.filtered_labels,
    }

  def to_dict(self, include_raw_labels=False):
    user = {
      'id': self.encrypted_id,
      'appId': SDKApp.encrypt_id(self.app_id),

      'name': self.name,
      'uniqueId': self.unique_id,
      'email': self.email,

      'latestVisit': self.date_to_api_date(self.last_accessed_time),
      'firstVisit': self.date_to_api_date(self.create_time),

      'stats': {
        'screens': self.monthly_screens,
        'taps': self.monthly_taps,
        'visits': self.monthly_visits,
        'seconds': self.monthly_seconds,
        'days': self.monthly_days_active_computed,
      },

      'labels': self.filtered_labels,
    }

    if include_raw_labels:
      user['rawLabels'] = self.labels

    return user


class SDKUserIncrementLog(APIModel):
  sdk_user = models.ForeignKey(SDKUser, on_delete=models.DO_NOTHING)
  create_time = models.DateTimeField()
  data = hstore_field.HStoreField(null=True)
