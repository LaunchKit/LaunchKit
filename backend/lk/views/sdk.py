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
import re

from django import forms

from backend.lk.logic import appstore
from backend.lk.logic import appstore_app_info
from backend.lk.logic import tokens
from backend.lk.logic import sdk_apps
from backend.lk.logic import session_user_labels
from backend.lk.logic.session_user_labels import CumulativeTimeUsed
from backend.lk.logic.session_user_labels import SessionFrequency
from backend.lk.views.base import api_response
from backend.lk.views.base import api_user_view
from backend.lk.views.base import bad_request
from backend.lk.views.base import not_found
from backend.lk.models import SDKApp
from backend.lk.models import SDKProduct
from backend.lk.models import SDKToken
from backend.util import lkforms


#
# PRODUCTS
#


# Creates a form with all products as optional booleans.
SDKProductForm = type('SDKProductForm', (forms.Form,),
    {product_name: lkforms.LKBooleanField(required=False)
     for product_name in SDKProduct.kinds()})


#
# SDK TOKENS
#


@api_user_view('GET')
def tokens_view(request):
  my_tokens = tokens.get_my_tokens(request.user)
  return api_response({
    'tokens': [t.to_dict() for t in my_tokens],
  })


@api_user_view('GET')
def token_view(request, token_id=None):
  token = tokens.get_my_token_by_encrypted_id(request.user, token_id)
  if not token:
    return not_found()

  return api_response({
    'token': token.to_dict(),
  })


@api_user_view('POST')
def token_create_view(request):
  token = tokens.generate_token(request.user)
  return api_response({
    'token': token.to_dict(),
  })


@api_user_view('POST')
def token_get_or_create_view(request):
  my_tokens = [t for t in tokens.get_my_tokens(request.user) if not t.expire_time]
  if my_tokens:
    token = my_tokens[0]
  else:
    token = tokens.generate_token(request.user)

  return api_response({
    'token': token.to_dict(),
  })


@api_user_view('GET', enable_logged_out=True)
def token_identify_view(request, token=None):
  token_obj = tokens.token_by_token(token)
  if not token_obj:
    return api_response({
      'valid': False
    })

  return api_response({
    'valid': True,
    'lastUsedTime': SDKToken.date_to_api_date(token_obj.last_used_time),
    'owner': {
      'id': token_obj.user.encrypted_id,
      'name': token_obj.user.short_name,
    },
  })


@api_user_view('POST')
def token_expire_view(request, token_id=None):
  token = tokens.get_my_token_by_encrypted_id(request.user, token_id)
  if not token:
    return not_found()

  tokens.expire_token(token)
  return api_response({
    'token': token.to_dict(),
  })


#
# SDK APPS
#


@api_user_view('GET', 'POST')
def apps_view(request):
  if request.method == 'GET':
    return _apps_view_GET(request)
  else:
    return _apps_view_POST(request)


class ListAppsForm(forms.Form):
  only_config_parents = lkforms.LKBooleanField(required=False)

  product = forms.ChoiceField(choices=SDKProduct.choices(), required=False)


def _apps_view_GET(request):
  form = ListAppsForm(request.GET)
  if not form.is_valid():
    return bad_request('Invalid list parameters.', errors=form.errors)

  cleaned_data = {k: v for k, v in form.cleaned_data.items() if k in request.GET}
  apps = sdk_apps.my_decorated_apps(request.user, **cleaned_data)

  return api_response({
    'apps': [a.to_dict() for a in apps],
  })


BUNDLE_RE = re.compile(r'^[a-zA-Z0-9-]+(\.[a-zA-Z0-9-]+)*$')

class CreateSDKAppForm(SDKProductForm):
  bundle_id = forms.RegexField(required=False, regex=BUNDLE_RE)
  display_name = forms.CharField(required=False, max_length=128)

  itunes_id = forms.CharField(required=False, max_length=128)
  itunes_country = forms.CharField(required=False, max_length=2)
  def clean_itunes_id(self):
    itunes_id = self.cleaned_data.get('itunes_id')
    bundle_id = self.cleaned_data.get('bundle_id')
    if itunes_id and bundle_id:
      raise forms.ValidationError('Cannot supply `bundle_id` and `itunes_id` together')
    return itunes_id

  config_parent_id = lkforms.LKEncryptedIdReferenceField(SDKApp, required=False)
  def clean_config_parent_id(self):
    config_parent = self.cleaned_data.get('config_parent_id')
    if config_parent and config_parent.config_parent_id:
      raise forms.ValidationError('Invalid config parent: cannot nest config parents')
    return config_parent


def _apps_view_POST(request):
  form = CreateSDKAppForm(request.POST)
  if not form.is_valid():
    return bad_request('Invalid create app parameters.', errors=form.errors)

  bundle_id = form.cleaned_data.get('bundle_id')
  if bundle_id:
    app = sdk_apps.create_or_fetch_sdk_app_with_bundle_id(request.user, bundle_id)
    if app.appstore_app:
      # Edge case: Creating app store app again later, from bundle ID
      appstore_app_info.decorate_app(app.appstore_app, app.appstore_app_country)

  else:
    itunes_id, country = form.cleaned_data.get('itunes_id'), form.cleaned_data.get('itunes_country')
    appstore_app = appstore.get_app_by_itunes_id(itunes_id, country)
    if not appstore_app:
      return bad_request('Invalid `itunes_id` or `itunes_country` provided.')
    app = sdk_apps.create_or_decorate_sdk_app_with_appstore_app(request.user, appstore_app)

  display_name = form.cleaned_data.get('display_name')
  if display_name:
    app.display_name = display_name
    app.save(update_fields=['display_name'])

  config_parent_app = form.cleaned_data.get('config_parent_id')
  if config_parent_app:
    app.config_parent = config_parent_app
    app.save(update_fields=['config_parent'])

  for sdk_product in SDKProduct.kinds():
    if sdk_product in request.POST:
      setattr(app, sdk_product, form.cleaned_data[sdk_product])
      app.save(update_fields=['products'])

  return api_response({
    'app': app.to_dict(),
  })



class EditSDKAppForm(SDKProductForm):
  itunes_id = forms.CharField(required=False, max_length=128)
  itunes_country = forms.CharField(required=False, max_length=2)
  def clean_itunes_country(self):
    itunes_id = self.cleaned_data.get('itunes_id')
    itunes_country = self.cleaned_data.get('itunes_country')
    if bool(itunes_country) != bool(itunes_id):
      raise forms.ValidationError('If providing `itunes_country`, please also provide `itunes_id`.')
    return itunes_id

  display_name = forms.CharField(required=False, max_length=128)

  super_freq = forms.ChoiceField(required=False, choices=SessionFrequency.choices())
  super_time = forms.ChoiceField(required=False, choices=CumulativeTimeUsed.choices())
  def clean_super_time(self):
    super_freq = self.cleaned_data.get('super_freq')
    super_time = self.cleaned_data.get('super_time')
    if bool(super_freq) != bool(super_time):
      raise forms.ValidationError('Please provide both `super_freq` and `super_time`.')
    return super_time

  config_parent_id = lkforms.LKEncryptedIdReferenceField(SDKApp, required=False)

  def clean(self):
    cleaned_data = self.cleaned_data
    if not (cleaned_data.get('display_name')
            or cleaned_data.get('itunes_country')
            or cleaned_data.get('super_freq')
            or cleaned_data.get('config_parent_id')
            or any(cleaned_data.get(p) is not None for p in SDKProduct.kinds())):
      raise forms.ValidationError('Please provide an app property to edit.')

    return cleaned_data


def single_app_view(*methods):
  def wrapped(fn):
    @functools.wraps(fn)
    def _single_card_view(request, app_id_or_bundle_id=None, **kwargs):
      app_id = SDKApp.decrypt_id(app_id_or_bundle_id)
      if not app_id:
        app_id = SDKApp.objects.filter(user=request.user,
            bundle_id=app_id_or_bundle_id).values_list('id', flat=True).first()

      app = sdk_apps.decorated_app_by_id(app_id)
      if not (app and app.user_id == request.user.id):
        return not_found()

      return fn(request, app, **kwargs)
    return api_user_view(*methods)(_single_card_view)
  return wrapped


@single_app_view('GET', 'POST')
def app_view(request, app):
  if request.method == 'GET':
    return _app_view_GET(request, app)
  else:
    return _app_view_POST(request, app)

def _app_view_GET(request, app):
  return api_response({
    'app': app.to_dict(),
  })

def _app_view_POST(request, app):
  form = EditSDKAppForm(request.POST)
  if not form.is_valid():
    return bad_request('Invalid edits provided.', errors=form.errors)

  if form.cleaned_data.get('itunes_country'):
    itunes_id, country = form.cleaned_data.get('itunes_id'), form.cleaned_data.get('itunes_country')
    appstore_app = appstore.get_app_by_itunes_id(itunes_id, country)
    if not appstore_app:
      return bad_request('Invalid `itunes_id` or `itunes_country` provided.')

    if app.appstore_app and app.appstore_app.id != appstore_app.id:
      return bad_request('Cannot change `itunes_id` once it is set.')

    app.itunes_country = country
    app.save(update_fields=['itunes_county'])

  display_name = form.cleaned_data.get('display_name') or None
  if 'display_name' in request.POST:
    # Allow removing this field to default to appstore info / bundle id.
    app.display_name = display_name
    app.save(update_fields=['display_name'])

  super_freq, super_time = form.cleaned_data.get('super_freq'), form.cleaned_data.get('super_time')
  if super_freq:
    session_user_labels.set_super_config(app, super_freq, super_time)

    # TODO(Taylor): Figure out a better place to set this.
    if not request.user.flags.has_super_users:
      request.user.set_flags(['has_super_users'])

  if 'config_parent_id' in request.POST:
    # can also be None if removing parent.
    app.config_parent = form.cleaned_data.get('config_parent_id')
    app.save(update_fields=['config_parent'])

  for sdk_product in SDKProduct.kinds():
    if sdk_product in request.POST:
      setattr(app, sdk_product, form.cleaned_data[sdk_product])
      app.save(update_fields=['products'])

  return api_response({
    'app': app.to_dict(),
  })


@single_app_view('GET')
def app_itunes_info_view(request, app):
  if app.appstore_app:
    appstore_app = app.appstore_app
    appstore_app_info.decorate_app(appstore_app, app.appstore_app_country)
  else:
    appstore_app = appstore.get_app_by_bundle_id(app.bundle_id, request.GET.get('country') or 'us')

  return api_response({
    'info': appstore_app and appstore_app.decorated_info.to_dict(),
  })
