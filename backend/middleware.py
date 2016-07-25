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
from django.http import HttpResponsePermanentRedirect


class SetRemoteAddrFromForwardedFor(object):
  def process_request(self, request):
    try:
      real_ip = request.META['HTTP_X_FORWARDED_FOR']
      # HTTP_X_FORWARDED_FOR can be a comma-separated list of IPs.
      # Take just the first one.
      real_ip = real_ip.split(',')[0]
    except KeyError:
      real_ip = request.META['REMOTE_ADDR']

    setattr(request, 'remote_addr', real_ip)


class SecureRequiredMiddleware(object):
  def process_request(self, request):
    my_host = request.META.get('HTTP_HOST')

    # Redirect HTTP to HTTPS for the domains we like...
    if my_host in settings.REDIRECT_INSECURE_DOMAINS and not request.is_secure():
      redirect_url = request.build_absolute_uri().replace('http://', 'https://')
      return HttpResponsePermanentRedirect(redirect_url)

    redirect_base_url = settings.UNDESIRABLE_DOMAINS.get(my_host)
    if not redirect_base_url:
      return None

    redirect_url = redirect_base_url + request.get_full_path().lstrip('/')
    return HttpResponsePermanentRedirect(redirect_url)

  def process_response(self, request, response):
    response['X-Frame-Options'] = 'SAMEORIGIN'
    if request.is_secure():
      response['Strict-Transport-Security'] = 'max-age=631138519'
    return response


class JSONPostMiddleware(object):
  def process_request(self, request):
    setattr(request, 'DATA', None)
    if request.method != 'POST':
      return None
    content_type = request.META.get('CONTENT_TYPE', '')
    if '/json' not in content_type:
      return None

    try:
      json_data = json.loads(request.body)
    except (ValueError, TypeError):
      json_data = None

    # TODO(Taylor): Allow returning of invalid codes here somehow?
    # Assuming each endpoint will validate its own data, however.
    if isinstance(json_data, dict):
      setattr(request, 'DATA', json_data)
