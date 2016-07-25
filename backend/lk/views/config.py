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

import re
import logging

from django import forms

from backend.lk.logic import runtime_config
from backend.lk.logic import tokens
from backend.lk.logic import sdk_apps
from backend.lk.models import ConfigKind
from backend.lk.models import RuntimeConfigRule
from backend.lk.models import MatchOperator
from backend.lk.models import ALL_USER_LABELS
from backend.lk.views.base import api_response
from backend.lk.views.base import api_user_view
from backend.lk.views.base import bad_request
from backend.lk.views.base import ok_response
from backend.lk.views.base import not_found
from backend.lk.views.base import unauthorized_request
from backend.util import lkforms


# FORMS


KEY_RE = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')
BUNDLE_RE = re.compile(r'^[a-zA-Z0-9-]+(\.[a-zA-Z0-9-]+)*$')
VERSION_RE = re.compile(r'^[\d\w.-]{1,32}$')
BUILD_RE = re.compile(r'^[\d\w.-]{1,32}$')

labels_joined = '(?:%s)' % ('|'.join(ALL_USER_LABELS))
USER_LABELS_RE = re.compile(r'^%s(,%s)+$' % (labels_joined, labels_joined))


class GetConfigForm(forms.Form):
  namespace = forms.CharField(required=False, max_length=16)

  def clean_namespace(self):
    value = self.cleaned_data.get('namespace')
    return value or None

  bundle_id = forms.RegexField(required=True, regex=BUNDLE_RE)
  version = forms.RegexField(required=False, regex=VERSION_RE)
  build = forms.RegexField(required=False, regex=BUILD_RE)
  ios_version = forms.RegexField(required=False, regex=BUILD_RE)
  debug = lkforms.LKBooleanField(required=False)
  sdk_user_labels = forms.RegexField(required=False, regex=USER_LABELS_RE)


class RuleTargetForm(GetConfigForm):
  version_match = forms.ChoiceField(required=False, choices=MatchOperator.choices())
  build_match = forms.ChoiceField(required=False, choices=MatchOperator.choices())
  ios_version_match = forms.ChoiceField(required=False, choices=MatchOperator.choices())



class CreateRuleForm(RuleTargetForm):
  def __init__(self, data):
    super(CreateRuleForm, self).__init__(data)
    self._keys = set(data.keys())

  key = forms.RegexField(required=True, regex=KEY_RE)
  kind = forms.ChoiceField(choices=ConfigKind.choices(), required=False)
  description = forms.CharField(required=False, max_length=2048)

  def clean(self):
    cleaned_data = super(CreateRuleForm, self).clean()
    # Remove any items not in the actual postbody.
    for k in cleaned_data.keys():
      if not cleaned_data[k] and k not in self._keys:
        del cleaned_data[k]
    return cleaned_data

class EditRuleForm(RuleTargetForm):
  bundle_id = forms.RegexField(required=False, regex=BUNDLE_RE)
  description = forms.CharField(required=False, max_length=2048)


class ValueForm(forms.Form):
  def __init__(self, kind, data):
    super(ValueForm, self).__init__(data)
    self._data = data
    self.kind = kind

  value = forms.CharField(required=False, max_length=1048)

  def clean_value(self):
    value = self.cleaned_data.get('value') or ''

    if self.kind == ConfigKind.INT:
      try:
        value = int(value)
      except ValueError:
        raise forms.ValidationError('Invalid value for "int" kind')

    elif self.kind == ConfigKind.FLOAT:
      try:
        value = float(value)
      except ValueError:
        raise forms.ValidationError('Invalid value for "float" kind')

    elif self.kind == ConfigKind.BOOL:
      if value not in ('1', '0', 'true', 'false'):
        raise forms.ValidationError('Invalid value for "bool" kind: expect true, false')
      value = value in ('1', 'true')

    elif self.kind == ConfigKind.STRING:
      pass

    else:
      # invalid kind will cause separate error; this ensures row cannot save.
      value = None

    return value

  def clean_description(self):
    description = self.cleaned_data.get('description')

    if description is None:
      return None
    else:
      return description


@api_user_view('GET', 'POST')
def configs_view(request):
  if request.method == 'POST':
    return _configs_view_POST(request)
  else:
    return _configs_view_GET(request)

def _configs_view_GET(request):
  form = RuleTargetForm(request.GET)
  if not form.is_valid():
    return bad_request('Invalid rule qualifiers', errors=form.errors)

  qualifiers = {k: v for k, v in form.cleaned_data.items() if k in request.GET}
  bundle_id = qualifiers['bundle_id']
  del qualifiers['bundle_id']
  rules = runtime_config.rules_for_user(request.user, bundle_id, **qualifiers)

  last_published_time_by_namespace = runtime_config.rules_published_status_for_bundle_id(request.user, qualifiers.get('bundle_id'))

  return api_response({
    'rules': [r.to_dict() for r in rules],
    'status': {namespace: RuntimeConfigRule.date_to_api_date(d)
               for namespace, d in last_published_time_by_namespace.items()},
  })

def _configs_view_POST(request):
  form = CreateRuleForm(request.POST)

  if not form.is_valid():
    logging.info('Invalid rules: %s POST: %s', dict(form.errors), dict(request.POST))
    return bad_request(message='Invalid rule parameters.', errors=form.errors)

  key = form.cleaned_data['key']
  del form.cleaned_data['key']

  bundle_id = form.cleaned_data['bundle_id']
  # Create the app row if it doesn't exist so we can populate the "my apps" dropdown.
  app = sdk_apps.decorated_app_by_bundle_id(request.user, bundle_id)
  if not app.config:
    app.config = True
    app.save(update_fields=['products'])

  rules = runtime_config.rules_for_user_key(request.user, key, bundle_id)

  kind = None
  if 'kind' in form.cleaned_data:
    kind = form.cleaned_data['kind']
    del form.cleaned_data['kind']
    if rules and rules[0].kind != kind:
      return bad_request('Key already exists as a different `kind`; cannot change type.')
  elif rules:
    kind = rules[0].kind

  if not kind:
    return bad_request('Please provide a `kind` for this key.')

  value_form = ValueForm(kind, request.POST)
  if not value_form.is_valid():
    return bad_request(message='Invalid rule `value`.', errors=form.errors)

  value = value_form.cleaned_data['value']

  rule = runtime_config.create_rule(request.user, key, kind, value, **form.cleaned_data)

  if not request.user.flags.has_config:
    request.user.set_flags(['has_config'])

  return api_response({
    'rule': rule.to_dict(),
  })


@api_user_view('GET', 'POST')
def config_rule_view(request, rule_id):
  rule = RuntimeConfigRule.objects.filter(
      id=RuntimeConfigRule.decrypt_id(rule_id),
      user_id=request.user.id).first()
  if not rule:
    return not_found()

  if request.method == 'POST':
    target_form = EditRuleForm(request.POST)
    if not target_form.is_valid():
      return bad_request('Invalid edit config values.', errors=target_form.errors)

    cleaned_data = target_form.cleaned_data

    if 'value' in request.POST:
      value_form = ValueForm(rule.kind, request.POST)
      if not value_form.is_valid():
        return bad_request('Invalid edit config values.', errors=value_form.errors)
      cleaned_data.update(value_form.cleaned_data)

    # strip out arguments that were not present in the actual POSTbody.
    cleaned_data = {k: v for k, v in cleaned_data.items() if k in request.POST}

    runtime_config.update_rule(rule, **cleaned_data)

  return api_response({
    'rule': rule.to_dict(),
  })


@api_user_view('GET', 'POST')
def config_rule_delete_view(request, rule_id):
  rule = RuntimeConfigRule.objects.filter(
      id=RuntimeConfigRule.decrypt_id(rule_id),
      user_id=request.user.id).first()
  if not rule:
    return not_found()

  runtime_config.update_namespace_status(rule.user, rule.bundle_id, rule.namespace)
  rule.delete()

  return ok_response()


@api_user_view('GET', enable_logged_out=True)
def config_interpolated_view(request):
  token_id = request.GET.get('token')

  if token_id:
    user = tokens.user_by_token(token_id)
  else:
    user = request.user

  if not (user and user.is_authenticated()):
    return unauthorized_request('Please provide `token` or `access_token`.')

  form = GetConfigForm(request.GET)
  if not form.is_valid():
    return bad_request('Invalid options for config interpolation', errors=form.errors)

  user_labels = form.cleaned_data.get('sdk_user_labels')
  if user_labels:
    user_labels = ','.split(user_labels)

  config = runtime_config.interpolated_config_for_user(
      user,
      form.cleaned_data['namespace'],
      form.cleaned_data['bundle_id'],
      version=form.cleaned_data['version'],
      build=form.cleaned_data['build'],
      ios_version=form.cleaned_data['ios_version'],
      debug=form.cleaned_data['debug'],
      sdk_user_labels=user_labels)

  return api_response({
    'config': config,
  })


@api_user_view('POST')
def publish_rules_view(request):
  bundle_id = request.POST.get('bundle_id')
  if not bundle_id:
    return bad_request('Please provide `bundle_id`.')

  user = request.user

  # TODO(Taylor): Rejigger this endpoint around app IDs?
  app = sdk_apps.decorated_app_by_bundle_id(user, bundle_id)
  runtime_config.publish_rules(user,
      source_bundle_id=app.bundle_id,
      destination_bundle_id=app.bundle_id)

  for child_app in app.decorated_config_children:
    runtime_config.publish_rules(user,
        source_bundle_id=app.bundle_id,
        destination_bundle_id=child_app.bundle_id)

  return api_response({
    'published': True,
  })
