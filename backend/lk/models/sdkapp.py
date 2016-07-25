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

import sys

from django.db import models
from djorm_pgarray.fields import TextArrayField

from backend.lk.models.apimodel import APIModel
from backend.lk.models.appstore_app import AppStoreApp
from backend.lk.models.super_user_config import DEFAULT_ALMOST_CONFIG_FREQ
from backend.lk.models.super_user_config import DEFAULT_ALMOST_CONFIG_TIME
from backend.lk.models.super_user_config import DEFAULT_SUPER_CONFIG_FREQ
from backend.lk.models.super_user_config import DEFAULT_SUPER_CONFIG_TIME
from backend.lk.models.users import User
from backend.util import enum
from backend.util import hstore_field
from backend.util import text


class SDKProduct(enum.Enum):
  # IMPORTANT: These correspond to properties on SDKApp below.
  CONFIG = 'config'
  SUPER_USERS = 'super_users'


def _default_super_config():
  return [DEFAULT_SUPER_CONFIG_FREQ, DEFAULT_SUPER_CONFIG_TIME]

def _default_almost_config():
  return [DEFAULT_ALMOST_CONFIG_FREQ, DEFAULT_ALMOST_CONFIG_TIME]


class SDKApp(APIModel):
  class Meta:
    app_label = 'lk'
    unique_together = ('user', 'bundle_id',)

  ENCRYPTED_ID_KEY_TOKEN = 'sdk-app'

  user = models.ForeignKey(User, related_name='+', on_delete=models.DO_NOTHING)
  create_time = models.DateTimeField(auto_now_add=True)
  update_time = models.DateTimeField(auto_now=True)
  latest_track_time = models.DateTimeField(null=True)

  display_name = models.CharField(max_length=128, null=True)
  bundle_id = models.CharField(max_length=128, null=False)

  latest_debug_version = models.CharField(max_length=24, null=True)
  latest_prod_version = models.CharField(max_length=24, null=True)

  appstore_app = models.ForeignKey(AppStoreApp, null=True, related_name='+', on_delete=models.DO_NOTHING)
  appstore_app_country = models.CharField(max_length=2, null=True)

  super_config = TextArrayField(default=_default_super_config, null=False)
  almost_config = TextArrayField(default=_default_almost_config, null=False)

  config_parent = models.ForeignKey('self', null=True, related_name='config_children', on_delete=models.DO_NOTHING)

  products = hstore_field.HStoreField(null=True)
  config = products.bool_property()
  super_users = products.bool_property()

  # Decorated properties.

  decorated_label_counts = None
  decorated_config_children = None

  @property
  def name(self):
    if self.display_name:
      return self.display_name
    if self.appstore_app:
      return self.appstore_app.name
    return self.bundle_id

  @property
  def short_name(self):
    return text.app_short_name(self.name)

  def to_dict(self):
    products = [p for p in (self.products or {}) if getattr(self, p)]

    app = {
      'id': self.encrypted_id,

      'bundleId': self.bundle_id,
      'iTunesId': self.appstore_app and self.appstore_app.itunes_id,

      'names': {
        'short': self.short_name,
        'full': self.name,
        'display': self.display_name,
      },
      'icons': {
        'small': self.appstore_app and self.appstore_app.public_small_icon,
        'medium': self.appstore_app and self.appstore_app.public_medium_icon,
      },

      'latestTrackTime': self.date_to_api_date(self.latest_track_time),
      'latestVersion': {
        'debug': self.latest_debug_version,
        'prod': self.latest_prod_version,
      },

      'products': products,
    }

    if self.super_users:
      super_freq, super_time = self.super_config
      app['super'] = {'freq': super_freq, 'time': super_time,}

    if self.decorated_label_counts is not None:
      # Return a simplified list here.
      app['stats'] = {
        'active': self.decorated_label_counts.get('active-1m', 0),
        'inactive': self.decorated_label_counts.get('inactive-1m', 0),
      }
      if self.super_users:
        app['stats']['super'] = self.decorated_label_counts.get('super', 0)
        app['stats']['almost'] = self.decorated_label_counts.get('almost', 0)
        app['stats']['fringe'] = self.decorated_label_counts.get('fringe', 0)


    if self.decorated_config_children:
      app['configChildren'] = [a.to_dict() for a in self.decorated_config_children]
    elif self.config_parent_id:
      app['configChild'] = True

    return app


for k in SDKProduct.kinds():
  # if this happens, new product was not added as property on sdkapp
  try:
    assert isinstance(getattr(SDKApp, k, None), hstore_field.HStoreProperty)
  except:
    print 'Add "%s" to SDKApp model' % k
    sys.exit(1)
