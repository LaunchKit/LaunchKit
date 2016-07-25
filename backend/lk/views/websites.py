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

from django import forms
from django.conf import settings

from backend.lk.models import AppWebsite
from backend.lk.models import AppWebsiteView
from backend.lk.models import AppWebsitePage
from backend.lk.models import User
from backend.lk.models import Image
from backend.lk.logic import appstore
from backend.lk.logic import websites
from backend.lk.views.base import api_response
from backend.lk.views.base import api_view
from backend.lk.views.base import api_user_view
from backend.lk.views.base import bad_request
from backend.lk.views.base import not_found
from backend.lk.views.base import ok_response
from backend.lk.views.base import unauthorized_request
from backend.util import lkforms
from backend.util import text


class AppWebsiteForm(lkforms.FieldsListForm):
  app_name = forms.CharField(min_length=0, max_length=256, required=False)
  tagline = forms.CharField(min_length=0, max_length=256, required=False)

  short_description = forms.CharField(min_length=0, max_length=500, required=False)
  long_description = forms.CharField(min_length=0, max_length=4000, required=False)
  keywords = forms.CharField(min_length=0, max_length=200, required=False)
  google_analytics_id = forms.RegexField(required=False, regex=re.compile(r'^UA-\d{6,12}-\d{1,3}$'))

  itunes_id = forms.RegexField(required=False, regex=re.compile(r'^[0-9]+$'))
  play_store_id = forms.RegexField(required=False, regex=re.compile(r'^[\w-]+(\.[\w-]+)*$'))
  waiting_list_link = forms.URLField(required=False)
  waiting_list_label = forms.CharField(min_length=0, max_length=100, required=False)

  itunes_campaign_token = forms.CharField(min_length=0, max_length=100, required=False)
  itunes_provider_token = forms.CharField(min_length=0, max_length=100, required=False)

  # TODO(keith) - might want better regex for support links...
  support_link = forms.RegexField(required=False, regex=re.compile(r'^(mailto:|https?://).+$'))
  blog_link = forms.URLField(required=False)
  login_link = forms.URLField(required=False)
  press_link = forms.URLField(required=False)
  terms_link = forms.URLField(required=False)
  privacy_link = forms.URLField(required=False)
  twitter_link = forms.URLField(required=False)
  facebook_link = forms.URLField(required=False)
  instagram_link = forms.URLField(required=False)
  custom_link = forms.URLField(required=False)
  custom_link_label = forms.CharField(min_length=0, max_length=100, required=False)

  disable_lk_branding = forms.BooleanField(required=False)
  mixpanel_badge = forms.BooleanField(required=False)

  domain = lkforms.LKDomainField(required=False)
  def clean_domain(self):
    domain = self.cleaned_data.get('domain')
    if domain and domain.endswith(settings.EMAIL_FROM_DOMAIN):
      raise forms.ValidationError('Invalid domain.')
    return domain

  primary_color = lkforms.LKColorField(required=False)
  font = forms.CharField(min_length=0, max_length=50, required=False)
  custom_css = lkforms.LKCSSField(required=False)

  frame_screenshots = forms.ChoiceField(choices=[
    ('no', 'No',),
    ('white', 'White phone',),
    ('black', 'Black phone',),
  ], required=False)

  icon_id = lkforms.LKEncryptedIdReferenceField(Image, required=False, filter_params={'kind': 'website-icon'})
  logo_id = lkforms.LKEncryptedIdReferenceField(Image, required=False, filter_params={'kind': 'website-logo'})
  background_id = lkforms.LKEncryptedIdReferenceField(Image, required=False, filter_params={'kind': 'website-background'})

  # "1", "2", "1color", "2color", "3", "4", "5", ...
  template = forms.CharField(min_length=1, max_length=7, required=True)


class EditAppWebsiteForm(AppWebsiteForm):
  def __init__(self, d):
    super(EditAppWebsiteForm, self).__init__(d)
    for k in self.fields:
      # make all fields optional
      self.fields[k].required = False


class AppWebsiteScreenshotsForm(forms.Form):
  iphone_screenshot_ids = lkforms.LKEncryptedIdReferenceListField(Image, required=False, max_length=10, filter_params={'kind': 'website-screenshot'})


class EditPageForm(lkforms.FieldsListForm):
  terms = forms.CharField(min_length=0, max_length=50000, required=False)
  privacy = forms.CharField(min_length=0, max_length=50000, required=False)
  support = forms.CharField(min_length=0, max_length=50000, required=False)


def _assign_properties_from_dict(obj, form_dict):
  for k, v in form_dict.items():
    existing_value = getattr(obj, k)
    if isinstance(existing_value, Image):
      existing_value.decrement_ref_count()
    if isinstance(v, Image):
      v.increment_ref_count()
    setattr(obj, k, v)


@api_user_view('GET', 'POST')
def websites_view(request):
  if request.method == 'POST':
    return _websites_view_POST(request)

  else:
    return _websites_view_GET(request)


def _websites_view_GET(request):
  websites = (
    AppWebsite.objects
      .filter(user=request.user)
      .exclude(delete_time__isnull=False)
      .order_by('-create_time')
  )

  return api_response({
    'websites': [w.to_dict() for w in websites],
  })


def _websites_view_POST(request):
  itunes_id = request.POST.get('itunes_id')
  country = request.POST.get('country', 'us')
  if itunes_id and country:
    itunes_app = appstore.get_app_by_itunes_id(itunes_id, country)
  else:
    itunes_app = None

  post_data = {
    'template': '1',
    'frame_screenshots': 'white',
  }

  # Create website from iTunes info.
  if itunes_app:
    name, tagline = text.app_name_tagline(itunes_app.name)

    post_data.update({
      'itunes_id': itunes_app.itunes_id,
      'country': itunes_app.country,

      'app_name': name,
      'tagline': tagline,
      'long_description': itunes_app.description,
    })

  for k, v in request.POST.items():
    post_data[k] = v or post_data.get(k, '')

  form = AppWebsiteForm(post_data)
  if not form.is_valid():
    logging.info('Website creation problem: %s', dict(form.errors))
    return bad_request('Invalid website data.', errors=form.errors)

  domain = form.cleaned_data.get('domain')
  if domain:
    in_use_website = AppWebsite.objects.filter(domain=domain).count()
    if in_use_website:
      return bad_request('Invalid website data', errors={'domain': ['Domain already in use.']})

  screenshots_form = AppWebsiteScreenshotsForm(request.POST)
  if not screenshots_form.is_valid():
    return bad_request('Invalid screenshots provided.')

  new_website = AppWebsite(user=request.user)
  _assign_properties_from_dict(new_website, form.cleaned_model_data())
  new_website.save()

  # ADD ASSOCIATED SCREENSHOTS

  iphone_screenshots = screenshots_form.cleaned_data.get('iphone_screenshot_ids', [])
  if iphone_screenshots:
    websites.update_website_screenshots(new_website, iphone_screenshots, 'iPhone')

  request.user.set_flags(['has_websites'])

  return api_response({
    'website': new_website.to_dict(),
  })


@api_user_view('GET', 'POST', enable_logged_out=True)
def website_view(request, website_id):
  if request.method == 'GET':
    return _website_view_GET(request, website_id)

  else:
    if not request.user.is_authenticated():
      return unauthorized_request()
    return _website_view_POST(request, website_id)


def _website_view_GET(request, website_id):
  website_id = AppWebsite.decrypt_id(website_id)
  if not website_id:
    return not_found()

  website = (
    AppWebsite.objects
      .filter(id=website_id)
      .select_related('icon', 'background', 'logo')
      .first()
  )
  if not website or website.delete_time:
    return not_found()

  get_website_and_pages = request.GET.get('get_website_and_pages', False)

  return api_response({
    'website': website.to_dict(get_website_and_pages),
  })


def _website_view_POST(request, website_id):
  website = AppWebsite.find_by_encrypted_id(website_id, user_id=request.user.id, for_update=True)
  if not website or website.delete_time:
    return not_found()

  # FORM VALIDATION

  form = EditAppWebsiteForm(request.POST)
  if not form.is_valid():
    logging.info('Website edit problem (id=%s): %s', website.encrypted_id, dict(form.errors))
    return bad_request('Invalid website data.', errors=form.errors)

  domain = form.cleaned_data.get('domain')
  if domain:
    in_use_website = AppWebsite.objects.filter(domain=domain).exclude(id=website.id).count()
    if in_use_website:
      return bad_request('Invalid website data', errors={'domain': ['Domain already in use.']})

  screenshots_form = AppWebsiteScreenshotsForm(request.POST)
  if not screenshots_form.is_valid():
    logging.info('Website screenshots problem (id=%s): %s', website.encrypted_id, dict(screenshots_form.errors))
    return bad_request('Invalid screenshots provided.', errors=screenshots_form.errors)

  # ASSIGN MODIFIED PROPERTIES

  # Only assign values that were actually passed in the POSTbody.
  _assign_properties_from_dict(website, form.cleaned_model_data(filter_values=request.POST))

  # UPDATE ASSOCIATED SCREENSHOTS

  iphone_screenshots = screenshots_form.cleaned_data.get('iphone_screenshot_ids', [])
  if iphone_screenshots:
    websites.update_website_screenshots(website, iphone_screenshots, 'iPhone')

  # UPDATE HOSTED PAGES
  hosted_pages = EditPageForm(request.POST)
  if not hosted_pages.is_valid():
    return bad_request('Invalid website data.', errors=hosted_pages.errors)

  for field in hosted_pages:
    # Check if this field was actually included in the POSTdata with this request.
    if field.name in request.POST:
      websites.create_or_update_hosted_page(website, field.name, field.value())

  website.save()
  return api_response({'website': website.to_dict()})


@api_user_view('GET')
def website_page_view(request, website_id, slug):
  return _website_page_view_GET(request, website_id, slug)

def _website_page_view_GET(request, website_id, slug):
  website_id = AppWebsite.decrypt_id(website_id)
  if not website_id:
    return not_found()

  website = (
    AppWebsite.objects
      .filter(id=website_id)
      .select_related('icon', 'background', 'logo')
      .first()
  )
  if not website or website.delete_time:
    return not_found()

  page = AppWebsitePage.objects.get(website=website_id, slug=slug)
  if not page:
    return not_found()

  return api_response({
    'website': website.to_dict(),
    'page': page.to_dict()
  })


@api_view('GET')
def website_page_by_domain_view(request, domain=None, slug=None):
  website = AppWebsite.objects.filter(domain=domain).first()
  if not website or website.delete_time:
    return not_found()

  page = None
  if slug:
    page = AppWebsitePage.objects.filter(website=website.id, slug=slug).first()
    if not page:
      return not_found()

  return api_response({
    'website': website.to_dict(),
    'page': page and page.to_dict(),
  })


@api_view('POST')
def get_example_website_view(request):
  itunes_id = request.POST.get('itunes_id')
  country = request.POST.get('country', 'us')

  if itunes_id:
    example_website = websites.example_from_itunes_id(itunes_id, country)
  else:
    example_website = websites.get_fancy_cluster_example()

  return api_response({
    'website': example_website
  })


@api_user_view('POST')
def check_domain_cname_view(request):
  domain = request.POST.get('domain', '')
  try:
    domain = lkforms.validate_domain(domain)
  except:
    domain = None

  if domain:
    correct, error_message = websites.check_domain_for_cname_record(domain)

  else:
    correct = False
    error_message = 'Invalid domain provided'

  return api_response({
    'correct': correct,
    'error': error_message,
  })


@api_user_view('POST')
def delete_website_view(request, website_id=None):
  website = AppWebsite.find_by_encrypted_id(website_id, user_id=request.user.id, for_update=True)

  if not website or website.delete_time:
    return not_found()

  websites.delete_website(website)

  return ok_response()


@api_view('POST')
def track_website_view_view(request):
  website_id = AppWebsite.decrypt_id(request.POST.get('website_id'))
  referer = request.POST.get('referer') or None
  if referer:
    referer = referer[:200]
  host = request.POST.get('host', '')[:64]
  user_agent = request.POST.get('user_agent', '')[:256]

  path = request.POST.get('path') or None
  if path:
    path = path[:256]

  view = AppWebsiteView(
    website_id=website_id,
    host=host,
    referer=referer,
    user_agent=user_agent,
    remote_ip=request.remote_addr,
    path=path,
  )
  view.save()

  return ok_response()
