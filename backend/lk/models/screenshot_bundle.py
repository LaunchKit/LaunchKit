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
from django.utils.text import slugify
from djorm_pgarray.fields import TextArrayField

from backend.lk.models.apimodel import APIModel
from backend.lk.models.image import Image
from backend.lk.models.screenshot_set import ScreenshotSet
from backend.lk.models.users import User


class ScreenshotBundle(APIModel):
  ENCRYPTED_ID_KEY_TOKEN = 'screenshot-bundle'

  user = models.ForeignKey(User, related_name='+', on_delete=models.DO_NOTHING)
  screenshot_set = models.ForeignKey(ScreenshotSet, related_name='+', on_delete=models.DO_NOTHING)

  create_time = models.DateTimeField(auto_now_add=True)
  access_count = models.IntegerField(default=0)
  last_accessed_time = models.DateTimeField(null=True)
  import_time = models.DateTimeField(null=True, db_index=True)
  hq = models.NullBooleanField(null=True)

  upload_ids = TextArrayField()
  upload_names = TextArrayField()

  url = models.URLField(max_length=256, null=True)
  size_bytes = models.BigIntegerField(default=0)
  files_count = models.IntegerField(default=0)

  @property
  def file_basename(self):
    safe_version =  re.sub(r'[^A-Za-z0-9._-]', '', self.screenshot_set.version) or 'unknown'
    return '%s_%s_%s' % (slugify(self.screenshot_set.name) or 'Screenshots', safe_version, self.screenshot_set.platform)


class ScreenshotBundleImage(APIModel):
  create_time = models.DateTimeField(auto_now_add=True)

  user = models.ForeignKey(User, related_name='+', on_delete=models.DO_NOTHING)
  screenshot_bundle = models.ForeignKey(ScreenshotBundle, related_name='+', on_delete=models.DO_NOTHING)
  image = models.ForeignKey(Image, related_name='+', on_delete=models.DO_NOTHING)

  filename = models.CharField(max_length=64)
