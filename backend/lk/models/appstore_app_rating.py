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
from djorm_pgarray.fields import ArrayField

from backend.lk.models.apimodel import APIModel
from backend.lk.models.appstore_app import AppStoreApp
from backend.util import hstore_field


class AppStoreAppRating(APIModel):
  class Meta:
    app_label = 'lk'
    index_together = ('app', 'create_time')

  create_time = models.DateTimeField(auto_now_add=True)

  app = models.ForeignKey(AppStoreApp, related_name='+', db_index=False, on_delete=models.DO_NOTHING)

  rating = models.FloatField()
  reviews_count = models.PositiveIntegerField()

  current_version_rating = models.FloatField()
  current_version_reviews_count = models.PositiveIntegerField()
