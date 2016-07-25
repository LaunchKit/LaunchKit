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


class SlackAccessToken(APIModel):
  class Meta:
    app_label = 'lk'
    # This should really be universally unique, but for testing's sake...
    unique_together = ('user', 'token')

  user = models.ForeignKey(User, related_name='+', on_delete=models.DO_NOTHING)

  create_time = models.DateTimeField(auto_now_add=True)
  invalidated_time = models.DateTimeField(null=True)

  # invalidated tokens become null
  token = models.CharField(max_length=512, null=True)
  scope = models.CharField(max_length=128, null=False)

  # for slack-webhook type connections
  webhook_data = hstore_field.HStoreField(null=True)
  webhook_url = webhook_data.string_property()
  webhook_channel = webhook_data.string_property()
  webhook_config_url = webhook_data.string_property()
