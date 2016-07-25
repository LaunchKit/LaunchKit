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

import json
import logging
import re
import urllib
import urllib2
from collections import namedtuple
from datetime import datetime
from datetime import timedelta

from django.conf import settings
from django.db import IntegrityError

from backend import celery_app
from backend.util import urlutil
from backend.lk.logic import exif
from backend.lk.models import Image


class ImageInfo(object):
  def __init__(self, url, info):
    self.url = url
    self.format = info['format']
    self.size_bytes = info['sizeBytes']

    width = info['width']
    height = info['height']

    exif_dict = info.get('exifData') or {}

    self.exif_data = exif.parse_from_dict(exif_dict)

    if self.exif_data.orientation_is_sideways():
      width, height = height, width

    self.width = width
    self.height = height

  def update_image(self, image):
    image.gae_image_url = self.url
    image.format = self.format
    image.size_bytes = self.size_bytes

    image.width = self.width
    image.height = self.height

    image.time_taken = self.exif_data.photo_time

    if self.exif_data.has_location():
      image.location_latitude = self.exif_data.latitude
      image.location_longitude = self.exif_data.longitude


class GAEUnavailableResponse(RuntimeError):
  pass


def fetch_image_urls_for_upload_ids(gae_upload_ids):
  code, response = _issue_appengine_request('GET', '/get_uploaded_image_urls',
      image_ids=','.join([str(long(i)) for i in gae_upload_ids]))

  if code != 200:
    logging.info('Could not fetch IDs: %d %s', code, response)
    raise GAEUnavailableResponse()

  return response['imageUrls']


AssignImageResult = namedtuple('AssignImageResult', ['success', 'server_error', 'bad_request'])

def assign_upload_and_update_image(gae_upload_id, image):
  if not image.id:
    raise RuntimeError('Must save image row first')

  code, response = _issue_appengine_request('POST', '/assign_uploaded_image',
      upload_id=gae_upload_id,
      table_name='lk_image', id=image.id)

  if code != 200:
    logging.info('Could not complete assignment: %d %s', code, response)
    return AssignImageResult(False, code >= 500, 400 <= code < 500)

  image_info = ImageInfo(response['url'], response['info'])
  image_info.update_image(image)
  image.save()

  return AssignImageResult(True, False, False)


def delete_photo(table_name, db_id):
  code, response = _issue_appengine_request('DELETE', '/%s/%s' % (table_name, db_id))
  return code in (200, 404)


def _issue_appengine_request(method, path, **kwargs):
  gae_url = settings.APP_ENGINE_PHOTOS_UPLOAD_BASE_PATH + path
  postbody = None
  if method == 'GET':
    gae_url = urlutil.appendparams(gae_url, **kwargs)
  else:
    postbody = urllib.urlencode(kwargs)
  gae_request = urllib2.Request(gae_url, postbody, {
    'X-LK-Secret': settings.APP_ENGINE_HEADER_SECRET,
  })
  gae_request.get_method = lambda: method

  try:
    result = urllib2.urlopen(gae_request, None, 30.0)
    code = 200
  except urllib2.HTTPError as e:
    if e.code >= 500:
      logging.info('GAE 500 response: %s', e.code)
    result = e
    code = e.code
  except urllib2.URLError as e:
    logging.info('GAE connection problem: %s', e)
    return -1, None

  result_content = result.read()

  try:
    json_dict = json.loads(result_content)
  except ValueError as e:
    if code < 500:
      logging.warn('Bad JSON response from GAE: %r', result_content)
    json_dict = None

  return code, json_dict


@celery_app.task(ignore_result=True)
def clean_up_deleted_images():
  deleted_images = Image.objects.filter(deleted=True)[:100]
  for image in deleted_images:
    if delete_photo('lk_image', image.id):
      try:
        image.delete()
      except IntegrityError as e:
        table_name = re.findall(r'referenced from table "(.+)"', '%s' % e)
        logging.warn('lk_image still referenced: %s (%s) -- un-deleting', image.id, table_name)
        Image.objects.filter(id=image.id).update(deleted=False, ref_count=1)

@celery_app.task(ignore_result=True)
def clean_up_expired_images(offset_timedelta=None):
  # These will be actually deleted by clean_up_deleted_images().
  cutoff = datetime.now() - timedelta(days=1)
  if offset_timedelta:
    cutoff += offset_timedelta

  Image.objects.filter(create_time__lt=cutoff, ref_count=0).update(deleted=True)
