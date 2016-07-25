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
from backend.util import text


class SDKToken(APIModel):
  ENCRYPTED_ID_KEY_TOKEN = 'client-token'

  user = models.ForeignKey(User, related_name='+', on_delete=models.DO_NOTHING)

  create_time = models.DateTimeField(auto_now_add=True)
  last_used_time = models.DateTimeField(null=True)
  expire_time = models.DateTimeField(null=True)

  token = models.CharField(max_length=44, null=False, unique=True)

  def save(self, *args, **kwargs):
    if not self.token:
      self.token = text.random_urlsafe_token(length=44)
    value = super(APIModel, self).save(*args, **kwargs)
    return value

  def to_dict(self):
    return {
      'id': self.encrypted_id,
      'token': self.token,
      'createTime': self.date_to_api_date(self.create_time),
      'lastUsedTime': self.date_to_api_date(self.last_used_time),
      'expireTime': self.date_to_api_date(self.expire_time),
    }
