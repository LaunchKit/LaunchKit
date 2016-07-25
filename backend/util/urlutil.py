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

import urlparse
import urllib

from django.conf import settings
from django.core.urlresolvers import reverse


def abs_reverse(route_name, **kwargs):
  """Generates an absolute URL with the same rules as standard Django
  "reverse" URL generation function.
  """
  path = reverse(route_name, **kwargs)
  return urlparse.urljoin(settings.SITE_URL, path)


def appendparams(base_url, **additional_params):
  """Given a URL 'http://www.google.com/?q=foo', and params bar="baz",
  returns a URL properly interpolating and URL-encoding new parameters
  into the querystring.

  >>> appendparams('http://www.google.com/?q=foo', q='bar', bar='baz')
  'http://www.google.com/?q=bar&bar=baz'
  >>> appendparams('http://www.google.com/', q='bar')
  'http://www.google.com/?q=bar'
  >>> appendparams('/foo', foo='bar baz')
  '/foo?foo=bar+baz'
  """
  fragment = None
  params = {}
  if '#' in base_url:
    base_url, fragment = base_url.split('#', 1)
  if '?' in base_url:
    base_url, params_string = base_url.split('?', 1)
    params = dict(urlparse.parse_qsl(params_string))
  for k, v in additional_params.items():
    if v is None:
      if k in params:
        del params[k]
    else:
      params[k] = v
  if params:
    base_url = '%s?%s' % (base_url, urllib.urlencode(params))
  if fragment:
    base_url = '%s#%s' % (base_url, fragment)
  return base_url
