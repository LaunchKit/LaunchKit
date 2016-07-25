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
from backend.lk.models.appstore_app import AppStoreApp
from backend.util import text
from backend.util import urlutil



def url2png_url(url, size='1000x600', max_width='800'):
    querystring = urllib.urlencode({
      'url': url,
      'viewport': size,
      'thumbnail_max_width': max_width,
    })
    md5sum = md5(querystring + settings.URL2PNG_SECRET_KEY).hexdigest()
    return 'https://api.url2png.com/v6/%s/%s/png/?%s' % (settings.URL2PNG_URL_KEY, md5sum, querystring)


class AppStoreReview(APIModel):
  class Meta:
    app_label = 'lk'
    index_together = ('app', 'create_time')
    index_together = ('app', 'appstore_review_id')

  ENCRYPTED_ID_KEY_TOKEN = 'review'

  appstore_review_id = models.BigIntegerField(unique=True)

  app = models.ForeignKey(AppStoreApp, related_name='+', db_index=False, on_delete=models.DO_NOTHING) # index covered by index_together
  app_version = models.CharField(max_length=16)

  create_time = models.DateTimeField(auto_now_add=True, db_index=True)
  invalidated_time = models.DateTimeField(null=True)

  # This is so we know whether the "create time" is actually accurate.
  initial_ingestion = models.BooleanField(default=False)
  author_reviewed_before = models.BooleanField(default=False)

  title = models.CharField(max_length=256)
  body = models.TextField()

  author_title = models.CharField(max_length=128)
  author_id = models.CharField(max_length=16, db_index=True)

  rating = models.PositiveIntegerField()

  country = models.CharField(max_length=2)

  @property
  def public_url(self):
    return '%sreviews/%s/' % (settings.SITE_URL, self.encrypted_id)

  @property
  def tweet_url(self):
    return '%stweet/' % self.public_url

  def tweet_text(self, has_photo=False, include_url=True):
    tweet_format = '%s Star Review: "%%s"' % self.rating

    trimmed_content_length = 140 - len(tweet_format % '')

    if include_url:
      tweet_format += ' %s' % self.public_url

    # there will be a link to the URL in this tweet, regardless of whether
    # it is included here.
    trimmed_content_length -= text.TCO_URL_LENGTH
    trimmed_content_length -= 1

    if has_photo:
      # if we have a photo, there will be another t.co URL in here.
      trimmed_content_length -= text.TCO_URL_LENGTH
      # - 1 here for space before the URL when tacked on to the end.
      trimmed_content_length -= 1

    # Now ellipsize the content inside the quotes if necessary.
    content = '%s: %s' % (self.title, self.body)
    if len(content) > trimmed_content_length:
      # - 1 here for ellipsis.
      content = u'%s…' % (content[:trimmed_content_length - 1]).rstrip()

    return tweet_format % content

  @property
  def twitter_share_url(self):
    try:
      # include URL manually here
      return urlutil.appendparams('https://twitter.com/share',
        text=self.tweet_text(include_url=False),
        url=self.public_url,
      )
    except UnicodeEncodeError:
      return None

  @property
  def rating_stars(self):
    return ''.join([u'★'] * self.rating)

  @property
  def rating_empty_stars(self):
    return ''.join([u'☆'] * (5 - self.rating))

  @property
  def author_url(self):
    return 'https://itunes.apple.com/us/reviews?userProfileId=%s' % self.author_id

  @property
  def author_search_url(self):
    return urlutil.appendparams('https://www.google.com/search',
        q='"%s" twitter OR facebook OR linkedin OR apple OR email' % self.author_title)

  @property
  def as_image(self):
    return url2png_url(self.public_url)

  @property
  def country_name(self):
    from backend.lk.logic.appstore import APPSTORE_COUNTRIES_BY_CODE
    country_name = 'N/A'
    if self.country:
      country_name = APPSTORE_COUNTRIES_BY_CODE[self.country]
    return country_name

  def to_dict(self):
    return {
      'id': self.encrypted_id,
      'country': self.country,
      'title': self.title,
      'body': self.body,
      'author': {
        'id': self.author_id,
        'title': self.author_title,
        'url': self.author_url,
        'searchUrl': self.author_search_url,
      },
      'rating': self.rating,
      'appId': AppStoreApp.encrypt_id(self.app_id),
      'appVersion': self.app_version,
      'publicUrl': self.public_url,
      'twitterShareUrl': self.twitter_share_url,
      'tweetUrl': self.tweet_url,
      'tweetText': self.tweet_text(has_photo=True),
      'imageUrl': self.as_image,
    }
