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
import urlparse

from google.appengine.api import images
from google.appengine.api import urlfetch
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.runtime import apiproxy_errors

from launchkit_images.models import LKImageUpload
from launchkit_images.basehandler import BaseHandler
from launchkit_images import util


PUBLIC_BLOBSTORE_UPLOAD_HANDLER_PATH = '/image_upload_blob'
PUBLIC_UPLOAD_FIELD_NAME = 'upload'


FORM_HTML = """
<html><body>
  <form action="%(action)s" method="POST" enctype="multipart/form-data">
    <input type="file" name="%(file_field)s">
    <button type="submit">Upload</button>
  </form>
</html></body>
"""


class PublicRedirectHandler(BaseHandler):
  is_internal_only = False

  def get(self):
    self._redirect('https://launchkit.io/?from_blobstore=1')


ACCEPTABLE_PREFIXES = ['https://launchkit.io/', 'http://localhost:', 'http://192.168.', 'http://127.0.0.1:']


class PublicHandler(BaseHandler):
  is_internal_only = False

  def dispatch(self):
    if not self.app.debug and self.request.POST:
      referer = self.request.headers.get('Referer')
      if not (referer and any(referer.startswith(ap) for ap in ACCEPTABLE_PREFIXES)):
        logging.warn('Unauthorized request from referer: %s ip: %s', referer, self.request.remote_addr)
        self._not_authorized()
        return
    super(PublicHandler, self).dispatch()


class PublicFileUploadHandler(PublicHandler):
  def options(self):
    # This allows the Allow-Origin header from the parent class to be returned.
    pass

  def _finish_upload(self, image_data, filename, content_type):
    image = images.Image(image_data=image_data)

    image.im_feeling_lucky()
    try:
      image.execute_transforms(parse_source_metadata=True, output_encoding=images.JPEG, quality=1)
    except images.BadRequestError as e:
      self._bad_request('Image probably too large')
      return
    except (images.BadImageError, images.NotImageError) as e:
      self._bad_request('Not an image')
      return

    image_metadata = image.get_original_metadata()
    image_width = image.width
    image_height = image.height

    image_format = None
    if image.format == images.JPEG:
      image_format = 'jpeg'
    elif image.format == images.PNG:
      image_format = 'png'
    elif image.format == images.WEBP:
      image_format = 'webp'
    elif image.format == images.GIF:
      image_format = 'gif'
    else:
      self._bad_request('Unsupported image format')
      return

    if self.app.debug:
      #
      # App Engine's local environment, powered by PIL, does not
      # automatically rotate served images like production does.
      # So, make it seem like it does.
      #
      orientation = image_metadata.get('Orientation', 1)
      degrees = 0;
      if (orientation == 3):
        degrees = 180
      elif (orientation == 6):
        degrees = 90
      elif (orientation == 8):
        degrees = -90
      if degrees:
        logging.info('Applying DEBUG-only image rotation.')
        image.rotate(degrees)
        image_data = image.execute_transforms()

    # This .replace() stuff here is a crazy hack. App Engine apparently has a hard time
    # parsing LONG blocks of uninterrupted multipart form data, so instead of actually
    # fixing the bug, we just add some newlines into the JSON blob so hopefully no
    # single line goes too far over the line. This is a terrible hack, I know.
    #
    # Also, this bug only manifests itself in production.
    image_metadata_json = json.dumps(image_metadata).replace('":', '":\n').replace('",', '",\n')
    headers, payload = util.encode_multipart_formdata({
      'image_metadata_json': image_metadata_json,
      'image_width': '%d' % image_width,
      'image_height': '%d' % image_height,
      'image_format': image_format,
    }, {
      PUBLIC_UPLOAD_FIELD_NAME: (filename, content_type, image_data,),
    })

    if 'Content-Length' in headers:
      del headers['Content-Length']
    headers['Referer'] = self.request.headers.get('Referer')

    blobstore_upload_url = blobstore.create_upload_url(PUBLIC_BLOBSTORE_UPLOAD_HANDLER_PATH)
    if self.app.debug:
      scheme, netloc, path, params, query, fragment = urlparse.urlparse(blobstore_upload_url)
      host, port = netloc.split(':')
      host = self.request.headers.get('host', 'localhost').split(':')[0]
      netloc = '%s:%s' % (host, port)
      blobstore_upload_url = urlparse.urlunparse([scheme, netloc, path, params, query, fragment])

    post_rpc = urlfetch.create_rpc(deadline=15)
    urlfetch.make_fetch_call(post_rpc, blobstore_upload_url,
        method='POST',
        payload=payload,
        headers=headers)

    try:
      json_result = post_rpc.get_result()
    except apiproxy_errors.RequestTooLargeError:
      self._bad_request('The image is too large', code=HTTP_CODE_TOO_LARGE)
      return
    except urlfetch.DownloadError:
      self._error('Error saving image to blobstore')
      return

    if json_result.status_code >= 500:
      self._error('Invalid response code from blobstore upload')
      return
    if json_result.status_code >= 400:
      self._bad_request('Invalid image data')
      return

    self.response.headers['Content-Type'] = json_result.headers['Content-Type']
    self.response.write(json_result.content)


class PublicPostbodyUploadHandler(PublicFileUploadHandler):
  def get(self):
    form_html = FORM_HTML % {
      'action': '/image_upload',
      'file_field': PUBLIC_UPLOAD_FIELD_NAME,
    }
    if self.app.debug:
      self._html(form_html)
    else:
      self._not_authorized()

  def post(self):
    uploaded_file = self.request.POST.get(PUBLIC_UPLOAD_FIELD_NAME)
    # NOTE: uploaded_file is FALSEY because someone is a nightmare programmer.
    if uploaded_file is None:
      self._bad_request('Include `%s` as a multipart file upload' % PUBLIC_UPLOAD_FIELD_NAME)
      return

    if not hasattr(uploaded_file, 'filename'):
      self._bad_request('Uploaded file should be a file.')
      return

    filename = uploaded_file.filename
    content_type = uploaded_file.headers.get('content-type')

    image_data = uploaded_file.file.read()

    self._finish_upload(image_data, filename, content_type)


class FetchRemoteImageUploadHandler(PublicFileUploadHandler):
  def post(self):
    fullsize_url = self.request.get('fullsize_url')
    if not fullsize_url:
      self._bad_request('No image URL!')
      return

    fetch_rpc = urlfetch.create_rpc(deadline=15)
    urlfetch.make_fetch_call(fetch_rpc, fullsize_url)
    try:
      image_result = fetch_rpc.get_result()
    except urlfetch.ResponseTooLargeError:
      self._bad_request('The image is too large', code=HTTP_CODE_TOO_LARGE)
      return
    except urlfetch.DownloadError:
      self._error('Error downloading image')
      return

    if image_result.status_code != 200:
      logging.warn('Invalid download status code: %s clusterphoto_id: %s clusteruseravatar_id: %s',
          image_result.status_code, clusterphoto_id, clusteruseravatar_id)
      self._bad_request('Invalid image response -- %s status code', image_result.status_code)
      return

    if not image_result.content:
      logging.warn('Not an image: clusterphoto_id: %s clusteruseravatar_id: %s',
          clusterphoto_id, clusteruseravatar_id)
      self._bad_request('Invalid image data -- zero length')
      return

    content_type = image_result.headers.get('Content-Type', '').lower()
    if not content_type:
      self._bad_request('Image has no content-type.')
      return

    filename = 'image'
    if 'jpeg' in content_type or 'jpg' in content_type:
      filename += '.jpg'
    elif 'png' in content_type:
      filename += '.png'
    elif 'gif' in content_type:
      filename += '.gif'

    self._finish_upload(image_result.content, filename, content_type)


class PublicBlobstoreFileUploadHandler(blobstore_handlers.BlobstoreUploadHandler, PublicHandler):
  def post(self):
    uploaded_blobs = self.get_uploads(PUBLIC_UPLOAD_FIELD_NAME)
    if not uploaded_blobs:
      self._bad_request('No file upload supplied.')
      return
    blob_info = uploaded_blobs[0]

    image_upload = LKImageUpload()
    image_upload.image_blob = blob_info.key()
    # Don't actually load this from the blob, because that takes a long time.
    image_upload.image_metadata_json = self.request.POST['image_metadata_json']
    image_upload.image_width = int(self.request.POST['image_width'])
    image_upload.image_height = int(self.request.POST['image_height'])
    image_upload.image_format = self.request.POST['image_format']
    image_upload.size_bytes = blob_info.size

    def fail():
      try:
        blobstore.delete(blob_info.key())
      except:
        pass
      self._json({'message': 'Failed to write the image to datastore.'}, code=502)

    try:
      image_url = images.get_serving_url(image_upload.image_blob.key())
    except:
      logging.exception('Could not generate image serving URL')
      fail()
      return

    if not self.app.debug:
      image_url = image_url.replace('http://', 'https://')
    elif ':9103' in image_url:
      # Make sure this is served through the dev proxy so
      # we get access-control-allow-origin set.
      image_url = image_url.replace(':9103', ':9102')

    image_upload.image_serving_url = image_url

    try:
      image_upload.put()
    except:
      logging.exception('Could not save blob to DB! %s', blob_info.key())
      fail()
      return

    self._json({
      'uploadId': image_upload.key().id(),
    })

