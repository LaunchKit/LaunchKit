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
from backend.lk.models.sdkapp import SDKApp
from backend.lk.models.sdkuser import SDKUser
from backend.lk.models.users import User


class SDKUserLabelChangeEvent(APIModel):
  user = models.ForeignKey(User, related_name='+', on_delete=models.DO_NOTHING)

  app = models.ForeignKey(SDKApp, related_name='+', on_delete=models.DO_NOTHING)
  sdk_user = models.ForeignKey(SDKUser, related_name='+', on_delete=models.DO_NOTHING)

  kind = models.CharField(max_length=32, null=True)
  label = models.CharField(max_length=32, null=True)

