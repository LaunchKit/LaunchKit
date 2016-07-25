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

import webapp2


SHARED_HEADER_NAME = 'X-LK-Secret'
SHARED_HEADER_SECRET = '00000000000000000000000000000000'


class BaseHandler(webapp2.RequestHandler):
  is_internal_only = True

  def dispatch(self):
    header_secret = self.request.headers.get(SHARED_HEADER_NAME)

    if not self.app.debug:
      # Don't do this in dev mode because we're running behind the dev proxy here,
      # which adds headers for all app engine responses.
      self.response.headers['Access-Control-Allow-Origin'] = '*'

    if header_secret == SHARED_HEADER_SECRET or self.app.debug or not self.is_internal_only:
      super(BaseHandler, self).dispatch()
    else:
      self._not_authorized()

  def _error(self, message):
    self._json({'message': message}, code=502)

  def _bad_request(self, message, code=400):
    self._json({'message': message}, code=code)

  def _not_found(self, message):
    self._json({'message': message}, code=404)

  def _not_authorized(self, message='Not authorized'):
    self._json({'message': message}, code=403)

  def _json(self, obj, code=200):
    self.response.status = code
    self.response.headers['Content-Type'] = 'application/json'
    self.response.write(json.dumps(obj))

  def _html(self, message, code=200):
    self.response.status = code
    self.response.headers['Content-Type'] = 'text/html'
    self.response.write(message)

  def _redirect(self, location):
    self.response.status = 302
    self.response.headers['Location'] = location
    self.response.write('Redirecting...')
