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
from backend.lk.models.sdkvisit import SDKVisit


class SDKTap(APIModel):
  visit = models.ForeignKey(SDKVisit, related_name='+', on_delete=models.DO_NOTHING)

  create_time = models.DateTimeField(auto_now_add=True)

  time = models.DateTimeField(null=False)
  x = models.FloatField(null=False)
  y = models.FloatField(null=False)
  orient = models.CharField(max_length=1)
