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

from backend.lk.models import AppStoreAppInfo
from backend.lk.logic import urlfetch
from backend.util import urlutil


class RateLimitedError(RuntimeError):
  pass


ALL_NUMERIC_RE = re.compile(r'^\d{6,}$')
ITUNES_URL_RE = re.compile(r'itunes\.apple\.com/.+/id(\d+)')

# Documentation here:
# https://www.apple.com/itunes/affiliates/resources/documentation/itunes-store-web-service-search-api.html
LOOKUP_URL = 'https://itunes.apple.com/%s/lookup'
SOFTWARE_ENTITIES = 'software,iPadSoftware,macSoftware'


def model_from_dict(d, country):
  info = AppStoreAppInfo(country=country)

  info.itunes_id = d['trackId']
  info.bundle_id = d['bundleId']

  if d['kind'] == 'mac-software':
    info.mac_software = 1

  info.name = d['trackName']
  info.description = d.get('description')
  info.release_notes = d.get('releaseNotes')

  info.version = d['version']

  info.icon_60 = d.get('artworkUrl60')
  info.icon_100 = d.get('artworkUrl100')
  info.icon_512 = d.get('artworkUrl512')

  info.category = d.get('primaryGenreId')

  info.price = d.get('price')
  info.currency = d.get('currency')

  info.size_bytes = long(d.get('fileSizeBytes', 0))

  info.rating = d.get('averageUserRating', 0)
  info.reviews_count = d.get('userRatingCount', 0)
  info.current_version_rating = d.get('averageUserRatingForCurrentVersion', 0)
  info.current_version_reviews_count = d.get('userRatingCountForCurrentVersion', 0)

  info.content_rating = d.get('contentAdvisoryRating')

  info.developer_id = d['artistId']
  info.developer_url = d.get('sellerUrl')
  info.developer_name = d['artistName']

  info.categories = [int(g) for g in d.get('genreIds', [])]

  info.screenshots = d.get('screenshotUrls', [])
  info.ipad_screenshots = d.get('ipadScreenshotUrls', [])

  info.release_date = datetime.strptime(d['releaseDate'], '%Y-%m-%dT%H:%M:%SZ')

  return info



def _lookup_fetch(remote_url):
  results_dict = {}
  retry = 0
  while not (results_dict and 'results' in results_dict):
    if retry >= 10:
      return None

    if retry:
      remote_url = urlutil.appendparams(remote_url, time=time.time())
      logging.info('Invalid response from lookup API: %s trying: %s', results_dict, remote_url)
      time.sleep(0.333 * retry)

    code, headers, results_dict = urlfetch.fetch(remote_url, cache_seconds=(60 * 60),
        should_cache_fn=lambda c, d: d and d.get('results'))

    if code == 403:
      raise RateLimitedError()

    retry += 1

  if code != 200:
    return None

  app_infos = results_dict['results']
  if not (app_infos and isinstance(app_infos, list)):
    return None

  return app_infos


def app_info_with_id(app_id, country):
  remote_url = urlutil.appendparams(LOOKUP_URL % country, id=app_id)
  app_infos = _lookup_fetch(remote_url)

  if not app_infos:
    return None

  app_info = app_infos[0]
  if app_info.get('kind') not in ('software', 'mac-software'):
    return None

  return model_from_dict(app_info, country)


def app_info_with_bundle_id(bundle_id, country):
  remote_url = urlutil.appendparams(LOOKUP_URL % country, bundleId=bundle_id)
  app_infos = _lookup_fetch(remote_url)

  if not app_infos:
    return None

  app_info = app_infos[0]
  if app_info.get('kind') not in ('software', 'mac-software'):
    return None

  return model_from_dict(app_info, country)


def related_app_infos_with_developer_id(developer_id, country):
  remote_url = urlutil.appendparams(LOOKUP_URL % country, id=developer_id, entity=SOFTWARE_ENTITIES)
  app_infos = _lookup_fetch(remote_url)
  if not app_infos:
    return []

  filtered = []
  app_ids = set()
  for app_info in app_infos:
    if app_info.get('kind') not in ('software', 'mac-software'):
      continue
    if app_info['trackId'] in app_ids:
      continue
    app_ids.add(app_info['trackId'])
    filtered.append(app_info)

  return [model_from_dict(app_info, country) for app_info in filtered]
