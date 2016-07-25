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

import logging
from datetime import datetime

from django.conf import settings
from django.db import transaction

from backend.lk.logic import appstore_fetch
from backend.lk.models import AppWebsiteScreenshot
from backend.lk.models import AppWebsitePage
from backend.util import dnsutil
from backend.util import text


def check_domain_for_cname_record(domain):
  cname, error_message = dnsutil.get_cname_for_domain(domain)
  if error_message:
    return False, error_message

  if cname != '%s.' % settings.HOSTED_WEBSITE_CNAME:
    return False, 'The CNAME value is set but incorrect'

  return True, None


def _short_description(long_description):
  if not long_description:
    return long_description

  return '%s...' % long_description[:180]


def example_from_itunes_id(itunes_id, country):
  info = appstore_fetch.app_info_with_id(itunes_id, country)
  app_name, app_tagline = text.app_name_tagline(info.name)

  example_website = {
    'id': 'example',
    'appName': app_name,
    'tagline': app_tagline,
    'longDescription': info.description,
    'shortDescription': _short_description(info.description),
    'itunesId': info.itunes_id,
    'images': {
      'screenshots': {'iPhone': [{'url': screenshot} for screenshot in info.screenshots]},
      'icon': {'url': info.icon_512},
    }
  }

  return example_website


def get_fancy_cluster_example():
  return {
    'id': 'example',
    'domain': 'cluster.co',
    'template': '',
    'appName': 'Cluster',
    'tagline': 'Privately share special moments with friends and family',

    'shortDescription': 'Cluster gives you a private space to share photos and memories with the people you choose, away from social media. Make your own groups and share pics, videos, comments, and chat!',

    'longDescription': u'Cluster makes it possible to create private groups where you share moments through photos and videos with the people you care about. Create a group with family, a group of friends, coworkers, people from your home town, or anyone else!\r\n\r\nGreat for:\r\n\u2022 New Moms! Share photos of a new baby with close friends and family without spamming everyone on other social networks\r\n\u2022 College Students! Share memories with friends not appropriate for Facebook\r\n\u2022 Families! Keep in touch even if you\u2019re not in the same place.\r\n\r\nTons of people already trust Cluster. Here\u2019s why:\r\n\r\n\u2022 Private & secure: Only invited members of the group can see what you post.\r\n\u2022 An app for everyone: Access Cluster through gorgeous mobile apps and the web.\r\n\u2022 Relevant notifications: Know when people you invited post new things to the group.',

    'keywords': 'private,group,social,network,space,family,album,photo,video,collaborative,shared,sharing,event,baby',
    'itunesId': '596595032',
    'playStoreId': 'com.getcluster.android',
    'supportLink': 'http://cluster.co/help',
    'termsLink': 'http://cluster.co/terms',
    'privacyLink': 'http://cluster.co/privacy',
    'primaryColor': '#0092F2',
    'font': 'Lato',
    'frameScreenshots': 'white',

    'images': {
      'logo': {'url':'https://cluster-static.s3.amazonaws.com/images/marketing/presskit/cluster-logo-white-v1f813d97.png'},
      'background': {'url':'https://cluster-static.s3.amazonaws.com/images/namespaces/default/homepage-billboard-v4bead2de.jpg'},
      'icon': {'url':'http://a1668.phobos.apple.com/us/r30/Purple3/v4/01/c6/f0/01c6f095-df15-7bd9-03f6-53dba727cc8b/mzl.clrnjwyb.png'},
      'screenshots':
        {'iPhone': [{'url':'http://a3.mzstatic.com/us/r30/Purple3/v4/46/6a/f0/466af0fb-f1d7-80b5-6d03-ccd36ad904ef/screen1136x1136.jpeg'},
                    {'url':'http://a2.mzstatic.com/us/r30/Purple3/v4/4d/41/8c/4d418cfe-a384-312b-f04f-ac336c3359ff/screen1136x1136.jpeg'},
                    {'url':'http://a5.mzstatic.com/us/r30/Purple5/v4/21/a6/5a/21a65abd-2f66-6265-1fb0-c08c72e403b3/screen1136x1136.jpeg'},
                    {'url':'http://a3.mzstatic.com/us/r30/Purple3/v4/a6/6d/4e/a66d4e25-d0f7-d1d0-05ab-edffa3899c14/screen1136x1136.jpeg'},
                    {'url':'http://a4.mzstatic.com/us/r30/Purple1/v4/33/a0/d0/33a0d056-1761-9c51-4bb7-35813eb14f1f/screen1136x1136.jpeg'},
                   ],
        }
    },
  }


@transaction.atomic
def update_website_screenshots(website, screenshot_images, platform):
  existing_screenshots = list(AppWebsiteScreenshot.objects.filter(website_id=website.id, platform=platform).order_by('order'))

  screenshot_image_ids = set([i.id for i in screenshot_images])
  screenshots_to_delete = [s for s in existing_screenshots
                           if s.image_id not in screenshot_image_ids]
  for screenshot in screenshots_to_delete:
    screenshot.image.decrement_ref_count()
    screenshot.delete()

  existing_by_image_id = {i.image_id: i for i in existing_screenshots}
  for i, image in enumerate(screenshot_images):
    order = i + 1
    if image.id in existing_by_image_id:
      screenshot = existing_by_image_id[image.id]
      if screenshot.order != order:
        screenshot.order = order
        screenshot.save()

    else:
      image.increment_ref_count()
      screenshot = AppWebsiteScreenshot(website=website, image=image, platform=platform, order=order)
      screenshot.save()


@transaction.atomic
def create_or_update_hosted_page(website, slug, body):
  hosted_page_titles = {
    'terms' : 'Terms and Conditions',
    'privacy' : 'Privacy Policy',
    'support' : 'Support',
  }

  page = AppWebsitePage.objects.filter(website=website, slug=slug).first()

  if page and body:
    page.body = body
    page.save()

  elif not page and body:
    AppWebsitePage.objects.create(website=website, slug=slug, body=body, title=hosted_page_titles[slug])

  elif page and not body:
    page.delete()


@transaction.atomic
def delete_website(website):
  screenshots = list(website.screenshots.all())
  for screenshot in screenshots:
    screenshot.image.decrement_ref_count()
    screenshot.delete()

  if website.icon:
    website.icon.decrement_ref_count()
    website.icon = None

  if website.logo:
    website.logo.decrement_ref_count()
    website.logo = None

  if website.background:
    website.background.decrement_ref_count()
    website.background = None

  # TODO(Taylor): Mark as deleted instead of actually deleting potentially huge number of rows
  # AppWebsiteView.objects.filter(website_id=website.id).delete()

  website.domain = None
  website.delete_time = datetime.now()
  website.save()
