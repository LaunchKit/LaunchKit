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

import urllib
from hashlib import md5

from django.conf import settings
from django.db import models

from backend.lk.models.apimodel import APIModel
from backend.lk.models.image import Image
from backend.lk.models.users import User
from backend.util import hstore_field
from backend.util import text
from backend.util import urlutil


def url2png_url(url, size='1200x800', max_width='1200'):
    querystring = urllib.urlencode({
      'url': url,
      'viewport': size,
      'thumbnail_max_width': max_width,
    })
    md5sum = md5(querystring + settings.URL2PNG_SECRET_KEY).hexdigest()
    return 'https://api.url2png.com/v6/%s/%s/png/?%s' % (settings.URL2PNG_URL_KEY, md5sum, querystring)


class ScreenshotSet(APIModel):
  ENCRYPTED_ID_KEY_TOKEN = 'screenshot-set'

  user = models.ForeignKey(User, related_name='+', null=True, on_delete=models.DO_NOTHING)

  create_time = models.DateTimeField(auto_now_add=True)
  update_time = models.DateTimeField(auto_now=True)
  delete_time = models.DateTimeField(null=True, default=None)

  name = models.CharField(max_length=128)
  version = models.CharField(max_length=32)

  shot_count = models.PositiveIntegerField()

  decorated_images = None

  data = hstore_field.HStoreField(null=True)
  platform = data.string_property()

  @property
  def public_url(self):
    return '%sscreenshots/%s' % (settings.SITE_URL, self.encrypted_id)

  @property
  def as_image(self):
    return url2png_url(self.public_url)

  @property
  def app_store(self):
    if self.platform == "Android":
      return "Google Play"
    return "App Store"

  def tweet_text(self):
    content_format = u"Creating app store images for %s was so simple using Screenshot Builder"
    trimmed_content_length = 140 - text.TCO_URL_LENGTH - 1 - len(content_format % '')

    # Now ellipsize the content inside the quotes if necessary.
    name_version = '%s %s' % (self.name, self.version)
    if len(name_version) > trimmed_content_length:
      # - 1 here for ellipsis.
      name_version = u'%s…' % name_version[:trimmed_content_length - 1]

    return content_format % name_version

  @property
  def twitter_share_url(self):
    try:
      return urlutil.appendparams('https://twitter.com/share', text=self.tweet_text(), url=self.public_url)
    except UnicodeEncodeError:
      return None

  def to_dict(self):
    set_dict = {
      'id': self.encrypted_id,
      'createTime': self.date_to_api_date(self.create_time),
      'updateTime': self.date_to_api_date(self.update_time),

      'name': self.name,
      'version': self.version,

      'imageUrl': self.as_image,

      'twitterShareUrl': self.twitter_share_url,

      'shotCount': self.shot_count,

      'platform': self.platform,
      'appStore': self.app_store,
    }

    if self.decorated_images:
      set_dict['previewImages'] = [i.to_dict() for i in self.decorated_images]

    return set_dict


class ScreenshotShot(APIModel):
  ENCRYPTED_ID_KEY_TOKEN = 'screenshot-shot'

  user = models.ForeignKey(User, related_name='+', null=True, on_delete=models.DO_NOTHING)
  screenshot_set = models.ForeignKey(ScreenshotSet, related_name='+', null=False, on_delete=models.DO_NOTHING)

  create_time = models.DateTimeField(auto_now_add=True)
  update_time = models.DateTimeField(auto_now=True)

  screenshot_image = models.ForeignKey(Image, related_name='+', null=False, on_delete=models.DO_NOTHING)
  background_image = models.ForeignKey(Image, related_name='+', null=True, on_delete=models.DO_NOTHING)

  config = hstore_field.HStoreField(null=True)

  label = config.string_property()
  label_position = config.string_property()

  font = config.string_property()
  font_size = config.int_property()
  font_weight = config.int_property()
  font_color = config.string_property()

  phone_color = config.string_property()
  background_color = config.string_property()

  tablet_is_landscape = config.bool_property()
  is_landscape = config.bool_property()

  def to_dict(self):
    return {
      'id': self.encrypted_id,
      'createTime': self.date_to_api_date(self.create_time),

      'screenshot': self.screenshot_image.to_dict(),
      'background': self.background_image and self.background_image.to_dict(),
      'backgroundColor': self.background_color,

      'overrides': self.get_overrides(),

      'label': self.label,
      'labelPosition': self.label_position,

      'font': self.font,
      'fontSize': self.font_size,
      'fontWeight': self.font_weight,
      'fontColor': self.font_color,

      'phoneColor': self.phone_color or 'black',

      'isLandscape': self.is_landscape
    }

  def get_overrides(self):
    overrides = ScreenshotShotOverride.objects.filter(screenshot_shot_id=self.id)
    devices = {}
    for override in overrides:
      devices[override.device_type] = override.to_dict()
    return devices

class ScreenshotShotOverride(APIModel):
  ENCRYPTED_ID_KEY_TOKEN = 'screenshot-override'

  screenshot_set = models.ForeignKey(ScreenshotSet, related_name='+', null=False, on_delete=models.DO_NOTHING)
  screenshot_shot = models.ForeignKey(ScreenshotShot, related_name='+', null=False, on_delete=models.DO_NOTHING)
  override_image = models.ForeignKey(Image, related_name='+', null=False, on_delete=models.DO_NOTHING)

  device_type = models.CharField(max_length=32)

  create_time = models.DateTimeField(auto_now_add=True)
  update_time = models.DateTimeField(auto_now=True)

  data = hstore_field.HStoreField(null=True)

  is_landscape = data.bool_property()

  class Meta:
    app_label = 'lk'
    unique_together = ('screenshot_shot', 'device_type')

  def to_dict(self):
    return {
      'imageUrl': self.override_image.image_url(),
      'deviceType': self.device_type,
      'orientation': self.is_landscape
    }

