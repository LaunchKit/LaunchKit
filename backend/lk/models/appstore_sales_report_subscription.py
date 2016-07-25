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
from backend.lk.models.users import User
from backend.util import hstore_field


class AppStoreSalesReportSubscription(APIModel):
  ENCRYPTED_ID_KEY_TOKEN = 'appstore-sales-report-sub'

  create_time = models.DateTimeField(auto_now_add=True)
  update_time = models.DateTimeField(auto_now=True)

  latest_report_date = models.DateField(null=True)

  user = models.ForeignKey(User, related_name='+', on_delete=models.DO_NOTHING)
  enabled = models.BooleanField(default=False)
  invalidated_time = models.DateTimeField(null=True)

  data = hstore_field.HStoreField(null=True)

  email = data.string_property()
  my_email = data.bool_property()
  slack_url = data.string_property()

  slack_channel_id = data.string_property()
  slack_channel_name = data.string_property()

  def to_dict(self):
    d = {
      'id': self.encrypted_id,
      'createTime': self.date_to_api_date(self.create_time),
    }
    if self.email:
      d['email'] = self.email
    if self.my_email:
      d['myEmail'] = True
    if self.slack_url:
      d['slackUrl'] = self.slack_url
    if self.slack_channel_name:
      d['slackChannel'] = {
        'name': self.slack_channel_name,
      }
    return d
