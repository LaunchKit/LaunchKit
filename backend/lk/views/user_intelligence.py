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

from django import forms

from backend.lk.logic import sdk_apps
from backend.lk.logic import sessions
from backend.lk.models import SDKApp
from backend.lk.models import SDKUser
from backend.lk.models import SDKVisit
from backend.lk.views.base import api_response
from backend.lk.views.base import api_user_view
from backend.lk.views.base import bad_request
from backend.lk.views.base import not_found
from backend.util import lkforms



class TopUsersForm(forms.Form):
  app_id = lkforms.LKEncryptedIdReferenceField(SDKApp, required=True)
  query = forms.CharField(required=False)
  sort_key = forms.ChoiceField(choices=[(k, k) for k in sessions.TOP_USER_SORTABLE_ATTRIBUTES], required=False)
  start_sdk_user_id = lkforms.LKEncryptedIdReferenceField(SDKUser, required=False)
  raw_labels = lkforms.LKBooleanField(required=False)


@api_user_view('GET')
def users_view(request):
  form = TopUsersForm(request.GET)
  if not form.is_valid():
    return bad_request('Invalid filter params', errors=form.errors)

  data = form.cleaned_data
  query = data.get('query')

  start_sdk_user = data.get('start_sdk_user_id')

  top_users = sessions.top_users(request.user,
      data['app_id'],
      data.get('sort_key') or 'last_accessed_time',
      query=query,
      start_sdk_user=start_sdk_user)

  raw_labels = bool(form.cleaned_data.get('raw_labels'))
  return api_response({
    'users': [t.to_dict(include_raw_labels=raw_labels) for t in top_users],
  })


@api_user_view('GET')
def user_view(request, sdk_user_id=None):
  user = request.user

  sdk_user = SDKUser.find_by_encrypted_id(sdk_user_id)
  if not sdk_user or sdk_user.user_id != user.id:
    return not_found()

  app = sdk_apps.decorated_app_by_id(sdk_user.app_id)
  raw_labels = request.GET.get('raw_labels') == '1'
  days_active = sessions.days_active_for_user(sdk_user)
  return api_response({
    'user': sdk_user.to_dict(include_raw_labels=raw_labels),
    'clientUser': sdk_user.to_client_dict(),
    'daysActive': days_active,
    'app': app.to_dict(),
  })



class LatestVisitsForm(forms.Form):
  update_time = lkforms.LKDateTimeField(required=False)
  limit = forms.IntegerField(min_value=1, max_value=250, required=False)
  sdk_user_id = lkforms.LKEncryptedIdReferenceField(SDKUser, required=False)


@api_user_view('GET')
def visits_view(request):
  form = LatestVisitsForm(request.GET)
  if not form.is_valid():
    return bad_request('Invalid filters', errors=form.errors)

  visits = (SDKVisit.objects
      .filter(user_id=request.user.id)
      .select_related('client_app,client_user,session')
      .order_by('-end_time'))

  end_time = form.cleaned_data.get('end_time')
  if end_time:
    visits = visits.filter(end_time__lt=end_time)

  sdk_user = form.cleaned_data.get('sdk_user_id')
  if sdk_user:
    visits = visits.filter(session__sdk_user=sdk_user)

  limit = form.cleaned_data.get('limit') or 50
  visits = visits[:limit]

  return api_response({
    'visits': [v.to_dict() for v in visits],
  })
