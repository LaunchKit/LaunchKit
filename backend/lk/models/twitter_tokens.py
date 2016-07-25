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


class TwitterAccessToken(APIModel):
  class Meta:
    app_label = 'lk'

  handle = models.CharField(max_length=15, null=False)

  create_time = models.DateTimeField(auto_now_add=True)
  invalidated_time = models.DateTimeField(null=True)

  token = models.CharField(max_length=100, null=False)
  token_secret = models.CharField(max_length=100, null=False)

  user = models.ForeignKey(User, related_name='twitter_access_tokens_set', on_delete=models.DO_NOTHING)
