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
from backend.util import text
from backend.util import hstore_field


class AppStoreReviewNotification(APIModel):
  app = models.ForeignKey(AppStoreApp, related_name='+', on_delete=models.DO_NOTHING)
  user = models.ForeignKey(User, related_name='+', on_delete=models.DO_NOTHING)

  create_time = models.DateTimeField(auto_now_add=True, db_index=True)

  data = hstore_field.HStoreField()

  email = data.string_property()
  my_email = data.bool_property()
  slack_channel_name = data.string_property()
  slack_webhook = data.bool_property()
  twitter_handle = data.string_property()

  reviews_count = data.int_property()
