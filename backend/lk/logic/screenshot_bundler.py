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

import errno
import logging
import math
import os
import os.path
import re
import shutil
import tempfile
import time
import urllib2
import urlparse
import zipfile
from collections import namedtuple
from contextlib import contextmanager
from datetime import datetime
from ssl import SSLError

from boto.exception import BotoClientError
from boto.exception import BotoServerError
from boto.s3.bucket import Bucket
from boto.s3.connection import S3Connection
from boto.s3.key import Key
from django.conf import settings
from django.db import transaction

from backend import celery_app
from backend.lk.logic import emails
from backend.lk.logic import gae_photos
from backend.lk.models import Image
from backend.lk.models import EmailToken
from backend.lk.models import ScreenshotBundle
from backend.lk.models import ScreenshotBundleImage
from backend.util import urlutil


# Note that the archive will probably be smaller, and that
# we need ~2x as much available disk space.
MAX_TOTAL_DOWNLOAD_BYTES = 512 * 1024 * 1024

ARCHIVES_AUTODELETE_AFTER_DAYS = 7

LOCAL_ARCHIVE_DIR = '/var/launchkit/'


def build_screenshot_bundle(screenshot_set, user, upload_ids, upload_names, hq=False):
  bundle = ScreenshotBundle(user=user, screenshot_set=screenshot_set, upload_ids=upload_ids, upload_names=upload_names, hq=hq)
  bundle.save()

  # add delay to allow transaction to commit, so this bundle ID exists when the task starts:
  _build_and_send_bundle.apply_async(args=[bundle.id], countdown=2.5)

  return bundle


def _signed_s3_download_url(url, file_basename):
  connection = S3Connection(settings.READONLY_S3_ACCESS_KEY_ID,
        settings.READONLY_S3_SECRET_ACCESS_KEY)
  archives_bucket = Bucket(connection=connection, name=settings.BUNDLES_S3_BUCKET_NAME)

  parsed = urlparse.urlparse(url)
  file_key = Key(bucket=archives_bucket, name=parsed.path)
  headers = {
    'response-content-disposition': 'attachment; filename=%s.zip' % file_basename
  }
  return file_key.generate_url(600, query_auth=True, response_headers=headers)


def _local_download_url(path):
  basename = os.path.basename(path)
  return '%sv1/screenshot_sets/archive_download/%s' % (settings.API_URL, basename)


def build_download_url(bundle):
  if bundle.url.startswith(LOCAL_ARCHIVE_DIR):
    download_url = _local_download_url(bundle.url)
  else:
    download_url = _signed_s3_download_url(bundle.url, bundle.file_basename)

  bundle.last_accessed_time = datetime.now()
  bundle.access_count += 1
  bundle.save(update_fields=['last_accessed_time', 'access_count'])

  return download_url


def send_bundle(bundle):
  email_token = EmailToken(kind=EmailToken.KIND_DOWNLOAD_BUNDLE, email=bundle.user.email)
  email_token.save()

  download_url = '%sscreenshots/dashboard/%s/download/' % (settings.SITE_URL, bundle.screenshot_set.encrypted_id)
  download_url = urlutil.appendparams(download_url, bundle=bundle.encrypted_id, token=email_token.token)

  emails.send_bundle_ready_email(bundle.user, bundle.screenshot_set, download_url)


def _write_archive_to_s3(bundle, src_filename):
  connection = S3Connection(settings.READWRITE_S3_ACCESS_KEY_ID,
      settings.READWRITE_S3_SECRET_ACCESS_KEY)
  bundles_bucket = Bucket(connection=connection, name=settings.BUNDLES_S3_BUCKET_NAME)
  path = '%s/Bundle-%s.zip' % (bundle.screenshot_set.encrypted_id, time.time())
  file_key = Key(bucket=bundles_bucket, name=path)

  attempts = 0
  while attempts < 3:
    attempts += 1
    try:
      logging.info('Uploading archive... (attempt: %d)', attempts)
      file_key.set_contents_from_filename(src_filename)
      return 'https://%s/%s' % (settings.BUNDLES_S3_BUCKET_NAME_HOST, path)

    except (BotoServerError, BotoClientError):
      logging.exception('Exception during archive upload!')
    except:
      logging.exception('Unknown exception during archive upload!')

  return None


def mkdir_p(path):
  try:
    os.makedirs(path)
  except OSError as e:
    if e.errno == errno.EEXIST and os.path.isdir(path):
      pass
    else:
      raise

def _write_archive_to_local(bundle, src_filename):
  basename = 'Bundle-%s-%d.zip' % (bundle.encrypted_id, time.time())
  dst_filename = os.path.join(LOCAL_ARCHIVE_DIR, basename)
  # Ensure this directory exists.
  mkdir_p(LOCAL_ARCHIVE_DIR)
  shutil.copyfile(src_filename, dst_filename)
  return dst_filename


# pylint: disable=E1102
@celery_app.task(queue='archive', acks_late=True, default_retry_delay=60)
def _build_and_send_bundle(bundle_id):
  bundle = ScreenshotBundle.objects.get(pk=bundle_id)

  if bundle.import_time:
    bundle_images = ScreenshotBundleImage.objects.filter(screenshot_bundle_id=bundle_id).select_related('image')
    image_urls = []
    for bundle_image in bundle_images:
      image_url = bundle_image.image.gae_image_url
      image_urls.append(image_url)
  else:
    try:
      image_urls = gae_photos.fetch_image_urls_for_upload_ids(bundle.upload_ids)
    except gae_photos.GAEUnavailableResponse:
      raise _build_and_send_bundle.retry()

  download_items = []
  for upload_name, image_url in zip(bundle.upload_names, image_urls):
    if '/_ah/img/' in image_url:
      # for local debug images, don't specify =s0, because quality gets degraded.
      full_image_url = image_url
    elif bundle.hq:
      # for an HQ bundle, request PNG format for the download.
      full_image_url = image_url + '=s0-rp'
    else:
      # for a JPEG download, add "l100" which should cause EXIF data to be
      # generated for this JPEG.
      full_image_url = image_url + '=s0-l100'
    item = DownloadItem(full_image_url, upload_name)
    download_items.append(item)

  with build_archive_file(download_items, bundle.file_basename) as items_count_archive_filename:
    items_count, archive_filename = items_count_archive_filename

    if settings.BUNDLES_S3_BUCKET_NAME and settings.READWRITE_S3_ACCESS_KEY_ID:
      final_url = _write_archive_to_s3(bundle, archive_filename)
    else:
      final_url = _write_archive_to_local(bundle, archive_filename)

    if not final_url:
      raise _build_and_send_bundle.retry()

    bundle.files_count = items_count
    bundle.url = final_url
    bundle.size_bytes = os.stat(archive_filename).st_size
    bundle.save()

  send_bundle(bundle)


#
# ACTUALLY DOWNLOAD AND ZIP REMOTE FILES
#

DownloadItem = namedtuple('DownloadItem', ['source_url', 'basename'])

@contextmanager
def build_archive_file(all_items, archive_folder_name):
  archive_dir = tempfile.mkdtemp(prefix='lk-archive')
  logging.info('Created archive directory: %s', archive_dir)

  total_bytes = 0
  try:
    last_index = -1
    files = []
    for i, item in enumerate(all_items):
      if not item.source_url:
        logging.warn('Invalid source URL for archive download: %s', item.source_url)
        continue

      filename = _download_file(item.source_url, os.path.join(archive_dir, item.basename))
      if not filename:
        logging.warn('Could not download file for archive: %s', item.source_url)
        continue

      files.append(filename)
      last_index = i

      total_bytes += os.stat(filename).st_size
      if total_bytes >= MAX_TOTAL_DOWNLOAD_BYTES:
        logging.info('Archive large (%d bytes) .. stopping', total_bytes)
        break

    # make an archive out of the directory
    archive_filename = os.path.join(archive_dir, 'archive.zip')
    with zipfile.ZipFile(archive_filename, 'w') as zipped_archive:
      for filename in files:
        arcfile = os.path.join(archive_folder_name, os.path.basename(filename))
        zipped_archive.write(filename, arcfile)

    yield last_index + 1, archive_filename

  finally:
    logging.info('Cleaning up archive...')
    # destroy directory
    shutil.rmtree(archive_dir)


def _download_file(url, filename_without_extension):
  logging.debug('Downloading %s...', url)

  attempts = 0
  while attempts < 3:
    attempts += 1
    try:
      return _download_file_no_retries(url, filename_without_extension)
    except (urllib2.URLError, SSLError) as e:
      if attempts == 3:
        logging.error('Error during download; aborting. %s (url: %s)', e, url)
        raise e


def _download_file_no_retries(url, filename_without_extension):
  try:
    req = urllib2.urlopen(url, None, 30.0)
  except urllib2.HTTPError as e:
    if e.code >= 500:
      # Cause a retry if it's a 500 (potentially temporary)
      raise e
    return None

  headers = dict((p[0].lower(), p[1]) for p in (re.split(r':\s+', header.strip()) for header in req.info().headers))

  content_type = headers.get('content-type')
  if 'jpg' in content_type or 'jpeg' in content_type:
    extension = '.jpg'
  elif 'gif' in content_type:
    extension = '.gif'
  elif 'png' in content_type:
    extension = '.png'
  elif 'mp4' in content_type:
    extension = '.mp4'
  else:
    logging.warn('Unknown download content-type: %s', content_type)
    extension = ''

  deduper = 0
  while True:
    filename = filename_without_extension
    if deduper:
      filename += ' (%d)' % deduper
    filename += extension
    try:
      with open(filename, 'r'):
        # If we actually find the file, continue in the loop and increment the counter
        deduper += 1
    except IOError:
      break

  CHUNK = 256 * 1024
  with open(filename, 'w+') as fp:
    while True:
      chunk = req.read(CHUNK)
      if not chunk:
        break
      fp.write(chunk)

  return filename


#
# Actually assign images in GAE so we can have them around.
#


@celery_app.task(ignore_result=True, max_retries=10, queue='gae')
def assign_upload_to_bundle_id_user_id(gae_id, filename, bundle_id, user_id):
  image = Image(kind='screenshot-exported', user_id=user_id, ref_count=1)
  # Need to get an ID.
  image.save()

  result = gae_photos.assign_upload_and_update_image(gae_id, image)
  if not result.success:
    image.delete()

    if result.bad_request:
      logging.warn('Failed to assign screenshot: %s to bundle %s', gae_id, bundle_id)
      return

    countdown_secs = math.pow(2, assign_upload_to_bundle_id_user_id.request.retries + 1)
    raise assign_upload_to_bundle_id_user_id.retry(countdown=countdown_secs)

  sbi = ScreenshotBundleImage(screenshot_bundle_id=bundle_id,
      user_id=user_id, image=image, filename=filename)
  sbi.save()


@celery_app.task(ignore_result=True)
def assign_bundle_images(limit=10):
  # Filter on URL to make sure the bundle is done being imported.
  bundles = list(ScreenshotBundle.objects.filter(url__isnull=False, import_time__isnull=True).order_by('id')[:limit])
  ScreenshotBundle.objects.filter(id__in=[b.id for b in bundles]).update(import_time=datetime.now())

  for bundle in bundles:
    for gae_image_id, filename in zip(bundle.upload_ids, bundle.upload_names):
      assign_upload_to_bundle_id_user_id.delay(gae_image_id, filename, bundle.id, bundle.user_id)
