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

import functools
import logging
import os.path
import re
from datetime import datetime
from datetime import timedelta

from django import forms
from django.conf import settings
from django.core.servers.basehttp import FileWrapper
from django.http import HttpResponse

from backend.lk.models import Image
from backend.lk.models import ScreenshotSet
from backend.lk.models import ScreenshotBundle
from backend.lk.logic import screenshots
from backend.lk.logic import screenshot_bundler
from backend.lk.logic import users
from backend.lk.views.base import api_response
from backend.lk.views.base import api_view
from backend.lk.views.base import api_user_view
from backend.lk.views.base import bad_request
from backend.lk.views.base import not_found
from backend.lk.views.base import ok_response
from backend.lk.views.base import unavailable_response
from backend.util import lkforms


#
# UPLOAD IMAGES FOR SCREENSHOTS AND BACKGROUNDS
#


ACCEPTABLE_PREFIXES = set([
  'http://localhost:',
  'http://192.168.',
  'http://127.0.0.1:',
  settings.SITE_URL,
])


def create_image_view(fn):
  @functools.wraps(fn)
  def _create_image_view(request):
    if settings.IS_PRODUCTION:
      referer = request.META.get('HTTP_REFERER', '')
      if not any(referer.startswith(ap) for ap in ACCEPTABLE_PREFIXES):
        logging.info('Blocked request with missing referer')
        return bad_request()

    try:
      gae_id = int(request.POST['upload_id'])
    except (KeyError, ValueError, TypeError):
      gae_id = None

    if not gae_id:
      return bad_request('Please include `upload_id`.')

    user = None
    if request.user.is_authenticated():
      user = request.user

    image_result = fn(gae_id, user)
    if image_result.bad_request:
      return bad_request('Invalid image provided.')

    if image_result.server_error:
      return unavailable_response()

    image = image_result.image
    return api_response({
      'image': image.to_dict()
    })

  return api_user_view('POST', enable_logged_out=True)(_create_image_view)

@create_image_view
def screenshot_images_view(gae_id, user):
  return screenshots.create_screenshot_with_gae_id(gae_id, user=user)

@create_image_view
def background_images_view(gae_id, user):
  return screenshots.create_background_with_gae_id(gae_id, user=user)

@create_image_view
def website_icon_images_view(gae_id, user):
  return screenshots.create_website_icon_with_gae_id(gae_id, user=user)

@create_image_view
def website_logo_images_view(gae_id, user):
  return screenshots.create_website_logo_with_gae_id(gae_id, user=user)

@create_image_view
def website_background_images_view(gae_id, user):
  return screenshots.create_website_background_with_gae_id(gae_id, user=user)

@create_image_view
def website_screenshot_images_view(gae_id, user):
  return screenshots.create_website_screenshot_with_gae_id(gae_id, user=user)


#
# CREATE SCREENSHOT SETS
#


VERSION_RE = re.compile(r'^[\d\w.-]{1,32}$')

class NewSetForm(forms.Form):
  name = forms.CharField(required=True, min_length=1, max_length=128)
  version = forms.RegexField(required=True, regex=VERSION_RE)
  platform = forms.ChoiceField(choices=[
    ('iOS', 'iOS Phones & Tablets',),
    ('Android', 'Android Phones & Tablets',),
  ], required=True)

class EditSetForm(forms.Form):
  name = forms.CharField(required=False, min_length=1, max_length=128)
  version = forms.RegexField(required=False, regex=VERSION_RE)


@api_user_view('GET', 'POST')
def screenshot_sets_view(request):
  if request.method == 'GET':
    my_sets = screenshots.get_my_sets(request.user)
    screenshots.decorate_with_preview_images(my_sets)
    return api_response({
      'sets': [s.to_dict() for s in my_sets],
    })

  form = NewSetForm(request.POST)
  if not form.is_valid():
    return bad_request('Invalid new set.', errors=form.errors)

  my_sets = screenshots.get_my_sets(request.user)

  if not request.user.flags.has_screenshot_builder:
    request.user.set_flags(['has_screenshot_builder'])

  new_set = screenshots.create_set(request.user,
      form.cleaned_data['name'], form.cleaned_data['version'], form.cleaned_data['platform'])
  return api_response({
    'set': new_set.to_dict(),
  })

@api_user_view('GET', 'POST', enable_logged_out=True)
def screenshot_set_view(request, set_id=None):
  if request.method == 'GET':
    return _screenshot_set_view_GET(request, set_id=set_id)
  else:
    return _screenshot_set_view_POST(request, set_id=set_id)

def _screenshot_set_view_GET(request, set_id=None):
  the_set, shots = screenshots.get_set_and_shots_by_encrypted_id(request.user, set_id, enable_logged_out=True)
  if not the_set:
    return not_found()

  return api_response({
    'set': the_set.to_dict(),
    'shots': [shot.to_dict() for shot in shots],
  })

def _screenshot_set_view_POST(request, set_id=None):
  my_set, shots = screenshots.get_set_and_shots_by_encrypted_id(request.user, set_id)

  form = EditSetForm(request.POST)
  if not form.is_valid():
    return bad_request('Invalid update set form data.', errors=form.errors)

  kwargs = {}
  if request.POST.get('version'):
    kwargs['version'] = form.cleaned_data['version']
  if request.POST.get('name'):
    kwargs['name'] = form.cleaned_data['name']

  screenshots.update_set(my_set, **kwargs)

  return api_response({
    'set': my_set.to_dict(),
  })


@api_user_view('POST')
def screenshot_set_delete_view(request, set_id=None):
  my_set, _ = screenshots.get_set_and_shots_by_encrypted_id(request.user, set_id)
  if not my_set:
    return not_found()

  screenshots.delete_my_set(request.user, my_set)

  return ok_response()

@api_user_view('POST')
def screenshot_set_duplicate_view(request, set_id=None):
  my_set, _ = screenshots.get_set_and_shots_by_encrypted_id(request.user, set_id)
  if not my_set or request.user.id != my_set.user.id:
    return bad_request('You dont have premissions.')

  form = NewSetForm(request.POST)
  if not form.is_valid():
    return bad_request('Invalid new set.', errors=form.errors)

  new_set = screenshots.duplicate_set(my_set, form.cleaned_data['name'], form.cleaned_data['version'], form.cleaned_data['platform'])

  return api_response({
    'set': new_set.to_dict()
  })



#
# CREATE+DOWNLOAD BUNDLES
#


@api_user_view('POST')
def screenshot_set_create_bundle_view(request, set_id=None):
  my_set, shots = screenshots.get_set_and_shots_by_encrypted_id(request.user, set_id,
      enable_logged_out=False)
  if not my_set:
    return not_found()

  upload_ids = request.POST.getlist('upload_id') or []
  try:
    upload_ids = [long(i) for i in upload_ids]
  except (ValueError, TypeError):
    logging.info('invalid upload_ids: %s (set id: %s)', upload_ids, set_id)
    return bad_request('Invalid `upload_id`, each should be long integer.')

  if not upload_ids:
    logging.info('upload ids: %s body: %s %s %s', upload_ids, request.body, request.POST, request.method)
    return bad_request('Invalid `upload_id`, each should be a GAE upload ID.')

  upload_names = filter(lambda n: n and n.strip(), request.POST.getlist('upload_name') or [])
  if len(upload_ids) != len(upload_names):
    logging.info('invalid upload_names: %s upload_ids: %s (set id: %s)', upload_ids, upload_names, set_id)
    return bad_request('Invalid `upload_name`, each should be an upload filename corresponding to the `upload_id` provided.')

  hq = request.POST.get('hq') == '1'
  bundle = screenshot_bundler.build_screenshot_bundle(my_set, request.user, upload_ids, upload_names, hq=hq)
  if not bundle:
    return unavailable_response()

  return api_response({
    'bundleId': bundle.encrypted_id,
  })


@api_user_view('GET')
def screenshot_set_bundle_status_view(request, bundle_id=None):
  bundle = ScreenshotBundle.find_by_encrypted_id(bundle_id, user_id=request.user.id)
  if not bundle:
    return not_found()

  if bundle.url:
    return api_response({'status': 'ready'})

  if bundle.create_time < datetime.now() - timedelta(minutes=30):
    return api_response({'status': 'error'})

  return api_response({'status': 'building'})


@api_user_view('GET', enable_logged_out=True)
def screenshot_set_download_bundle_view(request, set_id=None):
  set_id = ScreenshotSet.decrypt_id(set_id)
  if not set_id:
    return not_found()

  bundle_id = request.GET.get('bundle_id')
  bundle = ScreenshotBundle.find_by_encrypted_id(bundle_id, screenshot_set_id=set_id)
  if not bundle:
    return bad_request('Could not find that bundle.')

  # Enable logged-out user access by token.
  if not (request.user.is_authenticated() and request.user.id == bundle.user_id):
    token = request.GET.get('token')
    user = users.get_user_by_email_token(token)
    if (not user) or user.id != bundle.user_id:
      return bad_request('Invalid token for this bundle.')

  return api_response({
    'downloadUrl': screenshot_bundler.build_download_url(bundle),
  })


#
# SHOTS WITHIN A SCREENSHOT SET
#

class CreateUpdateShotForm(forms.Form):
  screenshot_image_id = lkforms.LKEncryptedIdReferenceField(Image, required=False)
  def clean_screenshot_image_id(self):
    image = self.cleaned_data.get('screenshot_image_id')
    if image and image.kind != 'screenshot':
      raise forms.ValidationError('Invalid image; not a screenshot.')
    return image

  background_image_id = lkforms.LKEncryptedIdReferenceField(Image, required=False)
  def clean_background_image_id(self):
    image = self.cleaned_data.get('background_image_id')
    if image and image.kind != 'background':
      raise forms.ValidationError('Invalid image; not a background.')
    return image

  label = forms.CharField(min_length=0, max_length=500, required=False)
  label_position = forms.ChoiceField(choices=[
    ('above', 'Cropped Device with Text Above',),
    ('below', 'Cropped Device with Text Below',),
    ('above_full_device', 'Full Device with Text Above',),
    ('below_full_device', 'Full Device with Text Below',),
    ('device', 'Full Device Only',),
    ('above_screenshot', 'Screenshot with Text Above',),
    ('below_screenshot', 'Screenshot with Text Below',),
    ('none', 'Screenshot Only'),
  ], required=False)

  font = forms.CharField(min_length=0, max_length=50, required=False)
  font_size = forms.IntegerField(required=False)
  font_weight = forms.IntegerField(required=False)
  font_color = lkforms.LKColorField(required=False)

  phone_color = forms.ChoiceField(choices=[
    ('white', 'White phone',),
    ('black', 'Black phone',),
    ('gold', 'Gold phone',),
    ('rose', 'Rose Gold phone',),
  ], required=False)
  background_color = lkforms.LKColorField(required=False)

  is_landscape = lkforms.LKBooleanField(required=False)


@api_user_view('POST')
def screenshot_set_add_shot_view(request, set_id=None):
  my_set = screenshots.get_set_by_encrypted_id(request.user, set_id)
  if not my_set:
    return not_found()

  if my_set.shot_count >= 5:
    return bad_request('Maximum number of shots in this set already.')

  form = CreateUpdateShotForm(request.POST)
  if not form.is_valid():
    logging.warn('Invalid shot data: %s', dict(form.errors))
    return bad_request('Invalid shot data.', errors=form.errors)

  if not form.cleaned_data.get('screenshot_image_id'):
    return bad_request('Please supply `screenshot_image_id`.')

  fields = form.cleaned_data
  post_keys = set(request.POST.keys())
  for key in fields.keys():
    if key not in post_keys:
      # default from the form
      del fields[key]

  fields['screenshot_image'] = fields['screenshot_image_id']
  del fields['screenshot_image_id']

  if 'background_image_id' in fields:
    fields['background_image'] = fields['background_image_id']
    del fields['background_image_id']

  shot = screenshots.create_shot_in_set(request.user, my_set, **fields)
  return api_response({
    'shot': shot.to_dict(),
  })

@api_user_view('GET', 'POST')
def screenshot_shot_view(request, set_id=None, shot_id=None):
  my_set, shots = screenshots.get_set_and_shots_by_encrypted_id(request.user, set_id)
  if not my_set:
    return not_found()

  shot = [s for s in shots if s.encrypted_id == shot_id]
  if not shot:
    return not_found()
  shot = shot[0]

  if request.method == 'GET':
    return api_response({
      'shot': shot.to_dict(),
    })

  form = CreateUpdateShotForm(request.POST)
  if not form.is_valid():
    return bad_request('Invalid update shot data.', errors=form.errors)

  fields = form.cleaned_data
  post_keys = set(request.POST.keys())
  for key in fields.keys():
    if key not in post_keys:
      # default from the form
      del fields[key]

  if 'screenshot_image_id' in fields:
    fields['screenshot_image'] = fields['screenshot_image_id']
    del fields['screenshot_image_id']

  if 'background_image_id' in fields:
    fields['background_image'] = fields['background_image_id']
    del fields['background_image_id']

  screenshots.update_shot(shot, **fields)

  return api_response({
    'shot': shot.to_dict(),
  })

@api_user_view('POST')
def screenshot_delete_shot_view(request, set_id=None, shot_id=None):
  my_set, shots = screenshots.get_set_and_shots_by_encrypted_id(request.user, set_id)
  if not my_set:
    return not_found()

  shot = [s for s in shots if s.encrypted_id == shot_id]
  if not shot:
    return not_found()
  shot = shot[0]

  screenshots.delete_shot_in_set(my_set, shot)

  return ok_response()


@api_user_view('POST')
def screenshot_create_override(request, set_id=None, shot_id=None, device_type=None):

  image_id = request.POST.get('image_id')

  # Check for shot & image
  my_shot, image = screenshots.get_shot_and_override_image_by_encrypted_id(request.user, shot_id, image_id);

  # return if they neither exist
  if not my_shot or not image:
    return not_found()

  # otherwise create / udate a unique override image for the specified device_type
  override_image = screenshots.create_or_update_override_image(my_shot.screenshot_set, my_shot, image, device_type)

  return api_response({
    'override':override_image.to_dict()
  })

@api_user_view('POST')
def screenshot_delete_override(request, set_id=None, shot_id=None, device_type=None):

  override = screenshots.get_shot_override_by_encrypted_id(request.user, shot_id, device_type)

  if not override:
    return not_found()

  screenshots.delete_override_image(override)

  return ok_response()


@api_view('GET')
def archive_download_view(request, basename=None):
  logging.info('basename: %s', basename)
  
  filename = os.path.join(screenshot_bundler.LOCAL_ARCHIVE_DIR, basename)
  if not os.path.isfile(filename):
    return not_found()

  if not os.path.abspath(filename).startswith(screenshot_bundler.LOCAL_ARCHIVE_DIR):
    return not_found()

  wrapper = FileWrapper(file(filename))
  response = HttpResponse(wrapper, content_type='application/zip')
  response['Content-Length'] = os.path.getsize(filename)
  response['Content-Disposition'] = 'attachment; filename=%s' % basename
  return response
