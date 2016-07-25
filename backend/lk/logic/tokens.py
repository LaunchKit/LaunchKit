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

from datetime import datetime
from datetime import timedelta

from django.core.cache import cache

from backend.lk.models import SDKToken
from backend.lk.models import User


def get_my_tokens(user, offset=0, limit=50):
  return list(SDKToken.objects.filter(user=user).order_by('-id')[offset:limit])


def get_my_token_by_encrypted_id(user, token_id):
  token = SDKToken.find_by_encrypted_id(token_id)
  if token and token.user_id == user.id:
    return token
  return None


def _cache_key(token_string):
  assert isinstance(token_string, basestring)
  return 'sdktoken:%s' % token_string


def generate_token(user):
  token = SDKToken(user=user)
  token.save()

  return token


def expire_token(token):
  token.expire_time = datetime.now()
  token.save(update_fields=['expire_time'])
  token = cache.delete(_cache_key(token.token))


def mark_token_used(token):
  now = datetime.now()
  if not token.last_used_time or token.last_used_time < now - timedelta(minutes=1):
    token.last_used_time = now
    token.save(update_fields=['last_used_time'])


TOKEN_CACHE_MINUTES = 5


def token_by_token(token_string):
  if not token_string:
    return None

  key = _cache_key(token_string)
  token = cache.get(key)
  if token:
    return token

  token_qs = SDKToken.objects.filter(token=token_string, expire_time__isnull=True)
  token = token_qs.first()
  if token:
    now = datetime.now()
    if not token.last_used_time or token.last_used_time < now - timedelta(minutes=TOKEN_CACHE_MINUTES):
      token.last_used_time = now
      token_qs.update(last_used_time=now)
    # Most sessions won't last very long.
    cache.set(key, token, 60 * TOKEN_CACHE_MINUTES)

  return token


def user_by_token(token_string):
  token = token_by_token(token_string)
  if not token:
    return None

  return User.get_cached(token.user_id)
