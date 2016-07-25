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
from django.db.models import F

from backend.lk.models.apimodel import APIModel
from backend.lk.models.users import User
from backend.util import hstore_field


class Image(APIModel):
  ENCRYPTED_ID_KEY_TOKEN = 'image'

  kind = models.CharField(max_length=32, null=True)

  user = models.ForeignKey(User, related_name='+', null=True, on_delete=models.DO_NOTHING)

  create_time = models.DateTimeField(auto_now_add=True)
  update_time = models.DateTimeField(auto_now=True)

  ref_count = models.PositiveIntegerField(default=0)
  deleted = models.BooleanField(default=False)

  time_taken = models.DateTimeField(null=True)

  data = hstore_field.HStoreField(null=True)

  location_latitude = data.float_property()
  location_longitude = data.float_property()

  gae_image_url = data.string_property()

  format = data.string_property()
  width = data.int_property()
  height = data.int_property()
  size_bytes = data.int_property()

  def increment_ref_count(self):
    Image.objects.filter(id=self.id).update(ref_count=F('ref_count') + 1)
    self.ref_count += 1

  def decrement_ref_count(self):
    Image.objects.filter(id=self.id).update(ref_count=F('ref_count') - 1)
    self.ref_count -= 1

  @property
  def extension(self):
    # TODO(Taylor): jpeg to jpg? etc.
    return self.format

  def image_url(self, width=None, height=None, quality=0):
    args = []
    if width is None and height is None:
      args.append('s0')
    else:
      if width:
        args.append('w%d' % width)
      if height:
        args.append('h%d' % height)
      if width and height:
        # crop the image rather than making it tiny
        args.append('c')
      if quality:
        # quality should be 0-100
        args.append('q%d' % quality)
    return self.gae_image_url + '=%s' % '-'.join(args)

  def to_dict(self):
    return {
      'id': self.encrypted_id,
      'width': self.width,
      'height': self.height,
      'imageUrls': {
        'small': self.image_url(width=200),
        'medium': self.image_url(width=640),
        'full': self.image_url(),
      }
    }
