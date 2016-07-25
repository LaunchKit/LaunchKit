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

from django.db import models

from backend.lk.models.apimodel import APIModel
from backend.lk.models.appstore_app import AppStoreApp
from backend.lk.models.users import User
from backend.lk.models.twitter_app_connection import TwitterAppConnection
from backend.util import hstore_field


class AppStoreReviewSubscription(APIModel):
  ENCRYPTED_ID_KEY_TOKEN = 'appstore-review-sub'

  create_time = models.DateTimeField(auto_now_add=True)
  update_time = models.DateTimeField(auto_now=True)

  user = models.ForeignKey(User, related_name='+', on_delete=models.DO_NOTHING)
  enabled = models.BooleanField(default=False)
  invalidated_time = models.DateTimeField(null=True)

  last_notification_time = models.DateTimeField(null=True)

  twitter_connection = models.OneToOneField(TwitterAppConnection, related_name='subscription', null=True)

  data = hstore_field.HStoreField(null=True)

  email = data.string_property()
  my_email = data.bool_property()
  slack_url = data.string_property()

  slack_channel_id = data.string_property()
  slack_channel_name = data.string_property()

  filter_good = data.bool_property()
  filter_very_good = data.bool_property()
  filter_app = models.ForeignKey(AppStoreApp, related_name='+', null=True, on_delete=models.DO_NOTHING)

  def to_dict(self):
    d = {
      'id': self.encrypted_id,
      'createTime': self.date_to_api_date(self.create_time),
      'lastNotificationTime': self.date_to_api_date(self.last_notification_time),
      'filter': {},
    }
    if self.email:
      d['email'] = self.email
    if self.my_email:
      d['myEmail'] = True
    if self.slack_url:
      d['slackUrl'] = self.slack_url
    if self.slack_channel_name:
      d['slackChannel'] = {
        'name': self.slack_channel_name
      }
    if self.twitter_connection_id:
      d['twitterHandle'] = self.twitter_connection.handle
    if self.filter_good:
      d['filter']['good'] = True
    if self.filter_very_good:
      d['filter']['veryGood'] = True
    if self.filter_app_id:
      d['filter']['app'] = self.filter_app.to_dict()
    return d
