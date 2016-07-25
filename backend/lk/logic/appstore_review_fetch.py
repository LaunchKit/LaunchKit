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
import re
import time
from datetime import datetime

from backend.lk.models import AppStoreReview
from backend.lk.logic import urlfetch
from backend.util import urlutil


class RateLimitedError(RuntimeError):
  pass


WAIT_BETWEEN_RETRIES = 0.25

REVIEWS_URL_FORMAT = 'http://itunes.apple.com/%(country)s/rss/customerreviews/id=%(app_id)s/page=%(page)s/sortBy=mostRecent/json'
MAX_FETCH_ATTEMPTS = 5

PAGE_RE = re.compile(r'/page=(\d+)/')


def fetch_reviews(app, country='us', page=1):
  has_next_page = False
  fetched_reviews = None
  i = 0

  url = REVIEWS_URL_FORMAT % {
    'app_id': app.itunes_id,
    'page': page,
    'country': country,
  }

  while fetched_reviews is None and i < MAX_FETCH_ATTEMPTS:
    if i > 0:
      url = urlutil.appendparams(url, invalid_response_cache_bust='%0.6f' % time.time())
      # Don't hammer the site when failing.
      time.sleep(WAIT_BETWEEN_RETRIES)
    i += 1

    code, headers, result = urlfetch.fetch(url)
    if code != 200 or not result:
      if code == 403:
        raise RateLimitedError()
      else:
        continue

    entry = result['feed'].get('entry')
    if not entry:
      # This is either a "no reviews at all for this app on this page" case,
      # or a bad potentially cached result on the apple feed side.
      continue

    if not isinstance(entry, list):
      # This is an invalid response that sometimes happen, and it appears to be
      # non-recoverable.
      logging.info('Bad+invalid+non-recoverable response for app: %s url: %s', app.bundle_id, url)
      break

    # Successful response's first entry is a description of the app for some reason.
    fetched_reviews = entry[1:]

    last_page_link = [link['attributes']['href']
                      for link in result['feed']['link']
                      if link['attributes']['rel'] == 'last'][0]
    last_page_int = int(PAGE_RE.findall(last_page_link)[0])
    has_next_page = last_page_int > int(page)

  if i > 1:
    if fetched_reviews is None:
      logging.info('FAILED to fetch reviews.  %s attempts. %s page %s', i, app.bundle_id, page)
    else:
      logging.info('SUCCESS fetching reviews. %s attempts. %s page %s', i, app.bundle_id, page)

  if fetched_reviews:
    fetched_reviews = [review_from_dict(app, d, country) for d in fetched_reviews]

  return has_next_page, fetched_reviews


"""
{
  author: {
    uri: {
      label: "https://itunes.apple.com/us/reviews/id106721045"
    },
    name: {
      label: "Egas semag"
    },
    label: ""
  },
  im:version: {
    label: "1.6"
  },
  im:rating: {
    label: "5"
  },
  id: {
    label: "688216376"
  },
  title: {
    label: "This is fun and requires some thinking so five stars"
  },
  content: {
    label: "Title says it all",
    attributes: {
      type: "text"
    }
  },
  link: {
    attributes: {
      rel: "related",
      href: "https://itunes.apple.com/us/review?id=400274934&type=Purple%20Software"
    }
  },
  im:voteSum: {
    label: "0"
  },
  im:contentType: {
    attributes: {
      term: "Application",
      label: "Application"
    }
  },
  im:voteCount: {
    label: "0"
  }
}
"""

MAX_VERSION_LENGTH = 16

def review_from_dict(app, d, country):
  r = AppStoreReview(app=app)
  r.appstore_review_id = long(d['id']['label'])

  if 'im:version' in d:
    version_string = (d['im:version']['label'])[:MAX_VERSION_LENGTH]
    if version_string != '0':
      r.app_version = version_string
  if not r.app_version:
    # If we don't know the version, use the latest version we know.
    r.app_version = (app.version and app.version[:MAX_VERSION_LENGTH]) or 'unknown'

  r.title = d['title']['label']
  r.body = d['content']['label']
  r.rating = int(d['im:rating']['label'])
  r.author_id = d['author']['uri']['label'].split('/reviews/id')[1]
  r.author_title = d['author']['name']['label']
  if len(r.author_title) > 64:
    logging.info('Long author title: %s (appstore_review_id %s)', r.author_title, r.appstore_review_id)
  r.country = country

  return r

