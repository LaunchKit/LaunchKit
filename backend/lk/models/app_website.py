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

from django.conf import settings
from django.db import models

from backend.lk.models.apimodel import APIModel
from backend.lk.models.image import Image
from backend.lk.models.users import User
from backend.util import hstore_field


class AppWebsite(APIModel):
  PLATFORMS = ['iPhone']
  ENCRYPTED_ID_KEY_TOKEN = 'appwebsites'

  domain = models.CharField(max_length=100, unique=True, null=True)

  user = models.ForeignKey(User, related_name='+', on_delete=models.DO_NOTHING)

  logo = models.ForeignKey(Image, related_name='+', null=True, on_delete=models.DO_NOTHING)
  background = models.ForeignKey(Image, related_name='+', null=True, on_delete=models.DO_NOTHING)
  icon = models.ForeignKey(Image, related_name='+', null=True, on_delete=models.DO_NOTHING)

  create_time = models.DateTimeField(auto_now_add=True, db_index=True)
  update_time = models.DateTimeField(auto_now=True)
  delete_time = models.DateTimeField(null=True, default=None)

  data = hstore_field.HStoreField(null=True)

  template = data.string_property()

  app_name = data.string_property()
  tagline = data.string_property()

  short_description = data.string_property()
  long_description = data.string_property()
  keywords = data.string_property()
  google_analytics_id = data.string_property()

  itunes_id = data.string_property()
  play_store_id = data.string_property()
  waiting_list_link = data.string_property()
  waiting_list_label = data.string_property()

  itunes_campaign_token = data.string_property()
  itunes_provider_token = data.string_property()

  support_link = data.string_property()
  blog_link = data.string_property()
  login_link = data.string_property()
  press_link = data.string_property()
  terms_link = data.string_property()
  privacy_link = data.string_property()
  twitter_link = data.string_property()
  facebook_link = data.string_property()
  instagram_link = data.string_property()
  custom_link = data.string_property()
  custom_link_label = data.string_property()

  disable_lk_branding = data.bool_property()
  mixpanel_badge = data.bool_property()

  terms_text = data.string_property()
  privacy_text = data.string_property()
  support_text = data.string_property()

  primary_color = data.string_property()
  font = data.string_property()
  frame_screenshots = data.string_property()

  custom_css = data.string_property()

  def to_dict(self, include_pages=False):
    screenshots = list(
      self.screenshots
          .select_related('image')
          .order_by('order')
    )

    screenshots_by_platform = {p: [] for p in self.PLATFORMS}
    for screenshot in screenshots:
      screenshots_by_platform[screenshot.platform].append(screenshot.to_dict())

    images = {
      'screenshots': screenshots_by_platform,
    }

    if self.icon:
      images['icon'] = {'id': self.icon.encrypted_id, 'url': self.icon.gae_image_url}
    if self.logo:
      images['logo'] = {'id': self.logo.encrypted_id, 'url': self.logo.gae_image_url}
    if self.background:
      images['background'] = {'id': self.background.encrypted_id, 'url': self.background.gae_image_url}

    website_data = {
      'id': self.encrypted_id,
      'domain': self.domain,
      'googleAnalyticsId': self.google_analytics_id,
      'template': self.template,
      'appName': self.app_name,
      'tagline': self.tagline,
      'shortDescription': self.short_description,
      'longDescription': self.long_description,
      'keywords': self.keywords,
      'author': self.user.full_name,
      'itunesId': self.itunes_id,
      'playStoreId': self.play_store_id,
      'waitingListLink': self.waiting_list_link,
      'waitingListLabel': self.waiting_list_label,
      'itunesCampaignToken': self.itunes_campaign_token,
      'itunesProviderToken': self.itunes_provider_token,
      'supportLink': self.support_link,
      'blogLink': self.blog_link,
      'loginLink': self.login_link,
      'pressLink': self.press_link,
      'termsLink': self.terms_link,
      'privacyLink': self.privacy_link,
      'twitterLink': self.twitter_link,
      'facebookLink': self.facebook_link,
      'instagramLink': self.instagram_link,
      'customLink': self.custom_link,
      'customLinkLabel': self.custom_link_label,
      'primaryColor': self.primary_color,
      'font': self.font,
      'disableLkBranding': self.disable_lk_branding,
      'mixpanelBadge': self.mixpanel_badge,
      'frameScreenshots': self.frame_screenshots,
      'images': images,
      'customCss': self.custom_css
    }


    pages = AppWebsitePage.objects.filter(website=self.id)
    for page in pages:
      if include_pages:
        website_data[page.slug] = page.body
      elif page.body:
        website_data[page.slug] = True

    return website_data

  @property
  def public_page_link(self):
    return '%swebsites/dashboard/%s/public/' % (settings.SITE_URL, self.encrypted_id)


class AppWebsiteScreenshot(APIModel):
  class Meta:
    app_label = 'lk'
    # TODO(Anyone) - we want this unique constraint, but it will break things.
    # unique_together = ('website', 'platform', 'order')

  website = models.ForeignKey(AppWebsite, related_name='screenshots', null=True, on_delete=models.DO_NOTHING)
  image = models.ForeignKey(Image, related_name='+', null=True, on_delete=models.DO_NOTHING)
  platform = models.CharField(max_length=15)
  order = models.PositiveSmallIntegerField()

  def to_dict(self):
    return {
      'imageId': self.image.encrypted_id,
      'url': self.image.gae_image_url,
    }

class AppWebsitePage(APIModel):
  class Meta:
    app_label = 'lk'
    unique_together = ('website', 'slug')

  website = models.ForeignKey(AppWebsite, related_name='page', null=False, on_delete=models.DO_NOTHING, db_index=False)
  slug = models.CharField(max_length=64, null=False)
  title = models.CharField(max_length=128, null=False)
  body = models.TextField()

  def to_dict(self):
    return {
      'title': self.title,
      'body': self.body
    }
