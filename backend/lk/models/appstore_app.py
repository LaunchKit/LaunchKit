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

import re

from django.db import models
from djorm_pgarray.fields import TextArrayField

from backend.lk.models.apimodel import APIModel


class AppStoreApp(APIModel):
  ENCRYPTED_ID_KEY_TOKEN = 'appstoreapp'

  create_time = models.DateTimeField(auto_now_add=True)
  update_time = models.DateTimeField(auto_now=True)

  itunes_id = models.CharField(max_length=128, unique=True)
  bundle_id = models.CharField(max_length=128, unique=True)

  app_info_ingestion_time = models.DateTimeField(null=True)
  app_info_countries = TextArrayField(null=True)

  decorated_country = None
  decorated_info = None
  def __getattr__(self, attr):
    return getattr(self.decorated_info, attr)

  @property
  def itunes_url(self):
    return 'https://itunes.apple.com/us/app/id%s' % self.itunes_id

  @property
  def public_small_icon(self):
    return self.icon_60

  @property
  def public_medium_icon(self):
    return self.icon_512

  def to_dict(self):
    return {
      'id': self.encrypted_id,
      'country': self.country,
      'version': self.version,

      'names': {
        'short': self.short_name,
        'full': self.name,
      },

      'icon': {
        'small': self.public_small_icon,
        'medium': self.public_medium_icon,
      },

      'iTunesId': self.itunes_id,
      'bundleId': self.bundle_id,

      'developer': self.developer_name,
    }
