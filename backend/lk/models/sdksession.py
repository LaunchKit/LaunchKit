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
from backend.lk.models.sdkapp import SDKApp
from backend.lk.models.sdkuser import SDKUser
from backend.util import hstore_field


class SDKSession(APIModel):
  class Meta:
    app_label = 'lk'
    index_together = (
      ('user', 'last_accessed_time'),
    )

  ENCRYPTED_ID_KEY_TOKEN = 'sdk-session'

  user = models.ForeignKey(User, related_name='+', on_delete=models.DO_NOTHING)
  create_time = models.DateTimeField(auto_now_add=True)
  last_upgrade_time = models.DateTimeField(auto_now_add=True, null=True)
  last_accessed_time = models.DateTimeField(auto_now_add=True)

  app = models.ForeignKey(SDKApp, related_name='+', on_delete=models.DO_NOTHING)
  app_version = models.CharField(max_length=32, null=True)
  app_build = models.CharField(max_length=32, null=True)
  app_build_debug = models.NullBooleanField(null=True)

  sdk_platform = models.CharField(max_length=8, null=True)
  sdk_version = models.CharField(max_length=32, null=True)

  os = models.CharField(max_length=3, null=True)
  os_version = models.CharField(max_length=16, null=True)
  hardware = models.CharField(max_length=32, null=True)

  screen_height = models.PositiveIntegerField(null=True)
  screen_width = models.PositiveIntegerField(null=True)
  screen_scale = models.FloatField(null=True)

  sdk_user = models.ForeignKey(SDKUser, null=True, on_delete=models.DO_NOTHING)

  screens = models.PositiveIntegerField(default=0)
  taps = models.PositiveIntegerField(default=0)
  visits = models.PositiveIntegerField(default=0)
  seconds = models.PositiveIntegerField(default=0)

  data = hstore_field.HStoreField(null=True)
