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
from djorm_pgarray.fields import IntegerArrayField
from djorm_pgarray.fields import TextArrayField

from backend.lk.models.apimodel import APIModel
from backend.lk.models.appstore_app import AppStoreApp
from backend.util import hstore_field
from backend.util import text


class AppStoreAppInfo(APIModel):
  create_time = models.DateTimeField(auto_now_add=True)

  app = models.ForeignKey(AppStoreApp, related_name='+', db_index=False, on_delete=models.DO_NOTHING)

  data = hstore_field.HStoreField()

  itunes_id = data.long_property()
  bundle_id = data.string_property()

  mac_software = data.bool_property()

  name = data.string_property()
  description = data.string_property()
  release_notes = data.string_property()

  version = data.string_property()

  icon_60 = data.string_property()
  icon_100 = data.string_property()
  icon_512 = data.string_property()

  category = data.int_property()

  price = data.float_property()
  currency = data.string_property()

  size_bytes = data.long_property()

  rating = data.float_property()
  reviews_count = data.int_property()

  current_version_rating = data.float_property()
  current_version_reviews_count = data.int_property()

  content_rating = data.string_property() # 4+, etc.

  developer_id = data.long_property()
  developer_url = data.string_property()
  developer_name = data.string_property()

  categories = IntegerArrayField()
  screenshots = TextArrayField()
  ipad_screenshots = TextArrayField(null=True)

  release_date = models.DateTimeField()

  country = models.CharField(null=True, max_length=2)

  @property
  def short_name(self):
    return text.app_short_name(self.name)

  def to_tiny_dict(self):
    return {
      'iTunesId': self.itunes_id,
      'name': self.name,
      'icon': {
        'small': self.icon_60,
      },
      'developer': {
        'id': self.developer_id,
        'name': self.developer_name,
      },
    }

  def to_dict(self):
    full_dict = self.to_tiny_dict()

    full_dict['bundleId'] = self.bundle_id

    full_dict['version'] = self.version
    full_dict['category'] = self.category
    full_dict['description'] = self.description
    full_dict['icon']['medium'] = self.icon_100
    full_dict['icon']['large'] = self.icon_512

    full_dict['developer']['url'] = self.developer_url

    full_dict['rating'] = self.rating
    full_dict['reviewCount'] = self.reviews_count
    full_dict['currentRating'] = self.current_version_rating
    full_dict['currentRatingStars'] = ''.join([u'★'] * int(self.current_version_rating))
    full_dict['currentReviewCount'] = self.current_version_reviews_count

    full_dict['screenshots'] = self.screenshots

    return full_dict
