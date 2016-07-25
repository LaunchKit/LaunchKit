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

import io
import logging
import ssl
import urllib
import urllib2
from socket import error as SocketError

import tweepy
from django.conf import settings

from backend.lk.models import TwitterAccessToken
from backend.lk.logic import redis_wrap


def get_auth_redirect(app_id=None, custom_cb=None):
  auth = get_auth_handler(app_id, custom_cb)
  try:
    redirect_url = auth.get_authorization_url()
  except tweepy.TweepError as e:
    logging.error('tweepy error getting auth url: %s', e)
    return None

  redis = redis_wrap.client()
  redis_key = get_redis_key(auth.request_token['oauth_token'])
  redis.setex(redis_key, 3600, auth.request_token['oauth_token_secret'])
  return redirect_url


def finish_auth(user, token, verifier):
  auth = get_auth_handler()
  redis = redis_wrap.client()
  redis_key = get_redis_key(token)
  token_secret = redis.get(redis_key)

  auth.request_token = {'oauth_token': token, 'oauth_token_secret': token_secret}
  try:
    auth.get_access_token(verifier)
  except tweepy.TweepError as e:
    logging.error('tweepy error during finish auth: %s', e)
    return False, None

  access_token = auth.access_token
  access_token_secret = auth.access_token_secret
  twitter_handle = auth.get_username()

  TwitterAccessToken.objects.get_or_create(
    handle=twitter_handle,
    token=access_token,
    token_secret=access_token_secret,
    user=user
  )

  return True, twitter_handle


def tweet_review(user, twitter_handle, review, custom_tweet_text=None):
  if twitter_handle not in user.twitter_handles:
    return False

  access_set = user.twitter_access_tokens_set.filter(handle=twitter_handle, invalidated_time__isnull=True).order_by('-id')
  if access_set:
    access = access_set[0]
  else:
    logging.error('No valid twitter credentials found for user %s trying to use handle %s', (user.id, twitter_handle))
    return False

  auth = get_auth_handler()
  auth.set_access_token(access.token, access.token_secret)
  try:
    api = tweepy.API(auth)
  except tweepy.TweepError as e:
    logging.error('tweepy error creating api: %s', e)
    return False

  if custom_tweet_text:
    tweet_text = custom_tweet_text
  else:
    tweet_text = review.tweet_text(has_photo=True)

  timeout = 10.0
  req = urllib2.Request(review.as_image, None, {})
  try:
    pic_file = io.BytesIO(urllib2.urlopen(req, None, timeout).read())
  except (urllib2.HTTPError, urllib2.URLError, ssl.SSLError, SocketError) as e:
    logging.warn('url2png connection problem: %s', e)
    return False

  try:
    api.update_with_media('screenshot.png', tweet_text, file=pic_file)
    return True
  except tweepy.TweepError as e:
    if e.message and isinstance(e.message, list) and isinstance(e.message[0], dict):
      error_code = e.message[0]['code']
    else:
      error_code = -1

    # TODO(Taylor): In this case, the token is bad and should be removed.
    # Sample error: [{u'message': u'Invalid or expired token.', u'code': 89}]
    if error_code not in (89, ):
      logging.error('tweepy error posting update with media: %s', e)

    return False


CALLBACK_URL = '%saccount/twitter/finish/' % settings.SITE_URL


def get_auth_handler(app_id=None, redirect_url=None):
  query = {}

  # if app_id is provided, automatically create subscription for app after successful twitter authentication
  if app_id:
    query['app_id'] = app_id

  # if redirect_url is provided, automatically redirect user to it afterwards
  if redirect_url:
    query['redirect_url'] = redirect_url

  cb = CALLBACK_URL
  if query:
    cb += '?%s' % urllib.urlencode(query)

  auth = tweepy.OAuthHandler(settings.TWITTER_CONSUMER_KEY, settings.TWITTER_CONSUMER_SECRET, cb)
  return auth


def get_redis_key(token):
  return 'twitter:%s' % token
