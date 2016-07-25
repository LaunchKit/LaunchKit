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
from backend.lk.models.appstore_app import AppStoreApp


class AppStoreAppReviewTracker(APIModel):
  class Meta:
    app_label = 'lk'
    unique_together = ('app', 'country')

  create_time = models.DateTimeField(auto_now_add=True)

  app = models.ForeignKey(AppStoreApp, on_delete=models.DO_NOTHING)
  country = models.CharField(max_length=2)

  last_ingestion_time = models.DateTimeField(null=True)
  latest_appstore_review_id = models.BigIntegerField(null=True)
  failed_ingestion_attempts = models.IntegerField(null=False, default=0)
  successful_ingestion_attempts = models.IntegerField(null=False, default=0)
  has_had_full_ingestion = models.BooleanField(default=False)
