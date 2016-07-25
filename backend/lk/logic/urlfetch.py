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

import collections
import json
import logging
import ssl
import time
import urllib2
from httplib import HTTPException
from socket import error as SocketError

from django.conf import settings
from django.core.cache import cache


CACHED_FETCH_KEY_FORMAT = 'cached-fetch:%s'


def send_request(url, method='GET', body=None, headers=None, json_response=True, timeout=8.0):
  headers = headers or {}
  headers.update({
    'User-Agent': 'Mozilla/5.0 (compatible; LK robot; +%s)' % settings.SITE_URL
  })
  req = urllib2.Request(url, body, headers)
  req.get_method = lambda: method

  try:
    result = urllib2.urlopen(req, None, timeout)
    code = 200
  except urllib2.HTTPError as e:
    if e.code >= 500:
      logging.warn('urlfetch response: %s', e.code)
    result = e
    code = e.code
  except SocketError as e:
    logging.info('urlfetch socket timeout or reset')
    return -1, {}, None
  except (urllib2.URLError, ssl.SSLError, HTTPException) as e:
    # HTTPException example: BadStatusLine ''
    logging.warn('urlfetch connection problem: %s', e)
    return -1, {}, None

  try:
    result_content = result.read()
  except SocketError as e:
    logging.warn('urlfetch socket error: %s', e)
    return -1, {}, None

  if json_response:
    try:
      result_content = json.loads(result_content)
    except ValueError as e:
      if code == 200:
        logging.warn('Invalid JSON response from URL: %s %r', url, result_content)
      result_content = None

  return code, result.info().dict, result_content


FetchResponse = collections.namedtuple('FetchResponse', ['code', 'headers', 'data'])

def fetch(url, cache_seconds=None, should_cache_fn=None, json_response=True, retries=0):
  if cache_seconds:
    cache_key = CACHED_FETCH_KEY_FORMAT % url
    cached = cache.get(cache_key)
    if cached:
      return cached

  code, headers, data = -1, {}, None
  for i in range(retries + 1):
    if i > 0:
      time.sleep(0.333 * i)
    code, headers, data = send_request(url, json_response=json_response)
    if code >= 200 and code < 500:
      break

  result = FetchResponse(code, headers, data)
  if cache_seconds and code >= 200 and code < 500:
    if (not should_cache_fn) or should_cache_fn(code, data):
      cache.set(cache_key, result, cache_seconds)

  return result