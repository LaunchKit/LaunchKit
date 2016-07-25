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
import json
import logging
import random
import time

from django.conf import settings
from django.core import exceptions
from django.db import IntegrityError
from django.db import connection
from django.http import HttpResponse
from django.http import UnreadablePostError


#
# API RESPONSES
#


def api_response(serializable_object, status=200):
  json_string = json.dumps(serializable_object)

  response = HttpResponse(json_string,
    content_type='application/json; charset=utf-8',
    status=status)
  response['Cache-Control'] = 'no-cache'
  response['X-API-Time'] = '%f' % time.time()

  if settings.DEBUG_SLOW_REQUESTS:
    time.sleep((0.5 * random.random()) + 0.2)

  return response

def ok_response():
  return api_response({'message': 'OK'})

def bad_request(message=None, errors=None, status=400):
  errors = errors or []
  return api_response({
    'message': message or 'Bad request',
    'errors': errors
  }, status=status)

def unauthorized_request(message=None):
  return api_response({'message': message or 'Unauthorized request'}, status=403)

def not_found(message=None, status=404):
  return api_response({'message': message or 'Not found'}, status=status)

def unavailable_response(message='Service unavailable', status=502):
  return api_response({'message': message}, status=status)


#
# API DECORATORS
#


def api_view(*methods):
  def wrapped(fn):
    @functools.wraps(fn)
    def _api_view(request, *args, **kwargs):
      if request.method not in methods:
        return api_response({'message': 'Method not allowed'}, status=405)

      try:
        return fn(request, *args, **kwargs)
      except exceptions.ObjectDoesNotExist as e:
        logging.exception('Object does not exist!')
        return not_found()
      except IntegrityError as e:
        logging.error('Database error in request: %s', e)
        return unavailable_response()
      except UnreadablePostError as e:
        logging.info('Aborted request')
        return unavailable_response('Aborted request')
      except Exception as e:
        logging.exception('Unknown exception in API method: %r', e)
        # Since we are not throwing the exception here, Django won't know to roll this back.
        connection._rollback()
        return unavailable_response()

    return _api_view
  return wrapped


def api_user_view(*methods, **dkwargs):
  enable_logged_out = dkwargs.get('enable_logged_out', False)
  def wrapped(fn):
    @functools.wraps(fn)
    def _api_user_view(request, *args, **kwargs):
      if not (enable_logged_out or (request.user.is_authenticated() and request.user.is_active)):
        return unauthorized_request()
      return fn(request, *args, **kwargs)
    return api_view(*methods)(_api_user_view)
  return wrapped
