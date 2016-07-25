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
from backend.lk.models.app_website import AppWebsite


class AppWebsiteView(APIModel):
  class Meta:
    app_label = 'lk'
    index_together = ('website', 'create_time')

  create_time = models.DateTimeField(auto_now_add=True, db_index=True)
  website = models.ForeignKey(AppWebsite, related_name='+', db_index=False, on_delete=models.DO_NOTHING)
  host = models.CharField(max_length=64)
  referer = models.URLField(null=True)
  user_agent = models.CharField(max_length=256)
  remote_ip = models.CharField(max_length=39, null=True)

  path = models.CharField(max_length=256, null=True)
