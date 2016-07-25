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

from django.conf import settings
from django.db import models

from backend.lk.models.apimodel import APIModel
from backend.lk.models.users import User
from backend.util import text


class OAuthAccessToken(APIModel):
  user = models.ForeignKey(User, related_name='+', on_delete=models.DO_NOTHING)
  client_id = models.CharField(max_length=32, choices=settings.OAUTH_CLIENT_CHOICES)

  token = models.CharField(max_length=66, null=False, unique=True)

  def save(self, *args, **kwargs):
    if not self.token:
      self.token = text.random_urlsafe_token(length=66)
    value = super(APIModel, self).save(*args, **kwargs)
    return value

  create_time = models.DateTimeField(auto_now_add=True)
  last_used_time = models.DateTimeField(auto_now_add=True)
  expire_time = models.DateTimeField(null=True, default=None, blank=True)

  scope = models.CharField(max_length=32, choices=settings.OAUTH_SCOPE_CHOICES)

