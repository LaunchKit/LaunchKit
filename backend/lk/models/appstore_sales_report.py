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
from backend.lk.models.itunes_connect_vendor import ItunesConnectVendor


class AppStoreSalesReport(APIModel):
  class Meta:
    app_label = 'lk'
    get_latest_by = 'end_date'

  app = models.ForeignKey(AppStoreApp, related_name='+', on_delete=models.DO_NOTHING)
  vendor = models.ForeignKey(ItunesConnectVendor, related_name='+', on_delete=models.DO_NOTHING)

  create_time = models.DateTimeField(auto_now_add=True)

  begin_date = models.DateField()
  end_date = models.DateField()

  product_type_identifier = models.CharField(max_length=20)
  units = models.DecimalField(max_digits=18, decimal_places=2)

  customer_currency = models.CharField(max_length=3)
  country_code = models.CharField(max_length=2)

  developer_proceeds = models.DecimalField(max_digits=18, decimal_places=2)
  proceeds_currency = models.CharField(max_length=3)

  provider = models.CharField(max_length=5)
  provider_country = models.CharField(max_length=2)

  sku = models.CharField(max_length=100)
  title = models.CharField(max_length=600)
  version = models.CharField(max_length=100)

  customer_price = models.DecimalField(max_digits=18, decimal_places=2)
  promo_code = models.CharField(max_length=10)

  subscription = models.CharField(max_length=10)
  period = models.CharField(max_length=30)

  parent_identifier = models.CharField(max_length=100)
  category = models.CharField(max_length=50)
  cmb = models.CharField(max_length=5)

  @property
  def is_download(self):
    return self.product_type_identifier in ['1', '1-B', '1E', '1EP', '1EU', '1F', '1T', 'F1']


class AppStoreSalesReportFetchedStatus(APIModel):
  class Meta:
    app_label = 'lk'
    unique_together = ('vendor', 'report_date')

  vendor = models.ForeignKey(ItunesConnectVendor, related_name='+', on_delete=models.DO_NOTHING)
  report_date = models.DateField()
  create_time = models.DateTimeField(auto_now_add=True)
  empty = models.BooleanField(default=False)
  failed = models.BooleanField(default=False)
