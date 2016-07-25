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
from backend.lk.models.itunes_connect_tokens import ItunesConnectAccessToken
from backend.lk.models.users import User


class ItunesConnectVendor(APIModel):
  class Meta:
    app_label = 'lk'
    unique_together = ('user', 'itc_id')

  ENCRYPTED_ID_KEY_TOKEN = 'itunesconnectvendor'

  user = models.ForeignKey(User, related_name='+', on_delete=models.DO_NOTHING)
  name = models.CharField(max_length=4000, null=False)
  itc_id = models.CharField(max_length=10)

  token = models.ForeignKey(ItunesConnectAccessToken, related_name='vendors', on_delete=models.DO_NOTHING)
  is_chosen = models.BooleanField(default=False)

  create_time = models.DateTimeField(auto_now_add=True)

  def to_dict(self):
    return {
      'id': self.encrypted_id,
      'name': self.name,
      'iTunesId': self.itc_id,
      'chosen': self.is_chosen,
    }
