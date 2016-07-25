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

from django.conf import settings
from django.http import HttpResponse

from backend.lk.logic import oauth


class FakeUser(object):
  def is_authenticated(self):
    return False


class OAuthAuthenticationMiddleware(object):
  def process_request(self, request):
    setattr(request, 'user', FakeUser())

    remote_ip = request.remote_addr
    is_local = (remote_ip in ('127.0.0.1', 'localhost'))

    if settings.IS_PRODUCTION and not (request.is_secure() or is_local):
      return None

    if hasattr(settings, 'OAUTH_PATH') and not request.path.startswith(settings.OAUTH_PATH):
      return None

    raw_token = None
    authorization = request.META.get('HTTP_AUTHORIZATION')
    if authorization and authorization.startswith('Bearer '):
      raw_token = authorization.replace('Bearer ', '')
    elif 'access_token' in request.GET:
      raw_token = request.GET['access_token']

    if not raw_token:
      return None

    user, scope = oauth.user_scope_for_token(raw_token)

    if not user:
      response_object = {
        'error_description': 'Please obtain a new access token.',
        'error': 'invalid_token',
      }
      response = HttpResponse(json.dumps(response_object),
        content_type='application/json; charset=utf-8',
        status=401)
      response['WWW-Authenticate'] = ('OAuth realm="LK API", error="invalid_token", '
                                      'error_description="The token provided is invalid."')
      response['Cache-Control'] = 'no-cache'
      return response

    if request.method != 'GET' and scope != settings.OAUTH_SCOPE_READWRITE:
      response_object = {
        'error_description': 'The token provided is not valid for write operations.',
        'error': 'insufficient_scope',
      }
      response = HttpResponse(json.dumps(response_object),
        content_type='application/json; charset=utf-8',
        status=405)
      response['WWW-Authenticate'] = ('Basic realm="LK API", error="insufficient_scope", '
                                      'error_description="The token provided is not valid for write operations."')
      response['Cache-Control'] = 'no-cache'
      return response

    # If all else works out, assign the user to the request.
    request.user = user

    return None
