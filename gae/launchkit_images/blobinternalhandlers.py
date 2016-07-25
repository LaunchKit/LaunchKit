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

from google.appengine.api import images
from google.appengine.api import urlfetch
from google.appengine.ext import blobstore
from google.appengine.ext import db
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.runtime import apiproxy_errors

from launchkit_images import util
from launchkit_images.basehandler import SHARED_HEADER_NAME
from launchkit_images.basehandler import SHARED_HEADER_SECRET
from launchkit_images.basehandler import BaseHandler
from launchkit_images.models import LKPhotoBlobstoreImage
from launchkit_images.models import LKImageUpload


HTTP_CODE_TOO_LARGE = 413


def _image_info_for_blob_key(blob_key):
  image = images.Image(blob_key=blob_key)
  # Execute a super low-quality transform so we can see just the size and not worry about everything else.
  image.im_feeling_lucky()
  image.execute_transforms(parse_source_metadata=True,
      output_encoding=images.JPEG,
      quality=1)
  return {
    'width': image.width,
    'height': image.height,
    'exifData': image.get_original_metadata(),
  }


def _info_handler_method(method):
  def info_handler_method(self, table_name, thing_id):
    try:
      thing_id = int(thing_id)
    except ValueError:
      thing_id = None

    if not thing_id:
      self._bad_request('Invalid ID provided')
      return

    key_name = LKPhotoBlobstoreImage.key_for_table_id(table_name, thing_id)
    stored_image = LKPhotoBlobstoreImage.get_by_key_name(key_name)

    if not stored_image:
      self._not_found('No image found with that ID')
      return

    return method(self, stored_image)

  return info_handler_method


class ImageInfoHandler(BaseHandler):
  @_info_handler_method
  def get(self, stored_image):
    image_json = _image_info_for_blob_key(stored_image.image_blob)
    self._json(image_json)

  @_info_handler_method
  def delete(self, stored_image):
    images.delete_serving_url(stored_image.image_blob.key())
    stored_image.image_blob.delete()
    stored_image.delete()
    self._json('OK')


class GetUploadedImageUrlsHandler(BaseHandler):
  def get(self):
    image_ids = self.request.get('image_ids')

    try:
      image_ids = [long(i) for i in (image_ids or '').split(',')]
    except (ValueError, TypeError) as e:
      pass

    if not image_ids:
      self._bad_request('Supply some image_ids')
      return

    image_keys = [db.Key.from_path('LKImageUpload', i) for i in image_ids]
    images = db.get(image_keys)

    self._json({'imageUrls': [i and i.image_serving_url for i in images]})


class AssignUploadedImageHandler(BaseHandler):
  def post(self):
    upload_id = self.request.get('upload_id')
    try:
      upload_id = long(upload_id)
    except (ValueError, TypeError):
      logging.info('Bad upload ID provided: %s', upload_id)
      self._bad_request('Invalid upload_id.')
      return

    table_name = self.request.get('table_name')
    thing_id = self.request.get('id')
    try:
      thing_id = int(thing_id)
    except (ValueError, TypeError):
      logging.info('Bad ID provided: %s', thing_id)
      self._bad_request('Invalid `id`.')
      return

    if not (table_name and thing_id):
      logging.info('Table + id not provided: %s %s', table_name, thing_id)
      self._bad_request('Provide `table_name` and `id`.')
      return

    image_upload = LKImageUpload.get_by_id(upload_id)
    if not image_upload:
      logging.info('Could not find upload id: %s', upload_id)
      self._bad_request('Could not find an upload with that upload_id.')
      return

    key_name = LKPhotoBlobstoreImage.key_for_table_id(table_name, thing_id)
    image_db = LKPhotoBlobstoreImage(key_name=key_name,
        table_name=table_name, db_id=thing_id)
    image_db.image_blob = image_upload.image_blob.key()
    image_db.size_bytes = image_upload.image_blob.size
    image_db.image_serving_url = image_upload.image_serving_url

    try:
      image_db.put()
      success = True
    except:
      logging.exception('Could not save blob to DB! upload id: %d', upload_id)
      success = False

    image_metadata_json = image_upload.image_metadata_json
    image_width = image_upload.image_width
    image_height = image_upload.image_height
    image_format = image_upload.image_format
    size_bytes = image_upload.size_bytes
    if image_metadata_json:
      image_metadata = json.loads(image_metadata_json)
    else:
      image_metadata = None

    try:
      image_upload.delete()
    except:
      logging.exception('Could not delete assigned upload')

    if not success:
      self._error('Failed to write blob to datastore.')
      return

    self._json({
      'url': image_db.image_serving_url,
      'info': {
        'width': image_width,
        'height': image_height,
        'format': image_format,
        'exifData': image_metadata,
        'sizeBytes': size_bytes,
      },
    })
