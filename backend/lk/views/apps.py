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

from backend.lk.models import AppStoreApp
from backend.lk.logic import appstore
from backend.lk.views.base import api_response
from backend.lk.views.base import api_user_view
from backend.lk.views.base import bad_request
from backend.lk.views.base import ok_response
from backend.lk.views.base import not_found


@api_user_view('GET', 'POST')
def apps_view(request):
  if request.method == 'GET':
    return _apps_view_GET(request)
  else:
    return _apps_view_POST(request)

def _apps_view_GET(request):
  my_apps = appstore.my_apps(request.user)
  return api_response({
    'apps': [a.to_dict() for a in my_apps],
  })

def _apps_view_POST(request):
  itunes_id = request.POST.get('itunes_id')

  country = request.POST.get('country')
  if not country or country not in appstore.APPSTORE_COUNTRIES_BY_CODE:
    return bad_request('Provide a valid `country`')

  if request.POST.get('include_related') == '1':
    apps = appstore.get_app_and_related_by_itunes_id(itunes_id, country)
    if not apps:
      return bad_request('Invalid `itunes_id` provided.')

  else:
    app = appstore.get_app_by_itunes_id(itunes_id, country)
    if not app:
      return bad_request('Invalid `itunes_id` provided.')

    apps = [app]

  appstore.mark_interested_in_apps(request.user, apps, country)

  return api_response({'apps': [a.to_dict() for a in apps]})


@api_user_view('POST')
def app_delete_view(request, country=None, app_id=None):
  app = AppStoreApp.find_by_encrypted_id(app_id)
  if not app:
    return not_found()

  if not country or country not in appstore.APPSTORE_COUNTRIES_BY_CODE:
    return not_found()

  success = appstore.mark_not_interested_in_app(request.user, app, country)
  if not success:
    return not_found()

  return ok_response()
