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

from backend.lk.models import User
from backend.lk.models import OAuthAccessToken

CACHE_KEY_FORMAT = 'lk_oauthaccesstoken:%s'


def create_token_for_user_client_scope(user, client_id, scope):
  access_tokens = OAuthAccessToken.objects.filter(user=user, client_id=client_id, scope=scope,
      expire_time__isnull=True).order_by('-create_time')[:1]
  if access_tokens:
    access_token = access_tokens[0]
  else:
    access_token = OAuthAccessToken(user=user, client_id=client_id, scope=scope)
    access_token.save()
  return access_token.token


def user_scope_for_token(raw_token):
  if not raw_token:
    return None

  token_cache_key = CACHE_KEY_FORMAT % raw_token
  token = cache.get(token_cache_key)

  if not token:
    try:
      token = OAuthAccessToken.objects.get(token=raw_token, expire_time__isnull=True)
    except OAuthAccessToken.DoesNotExist:
      token = None

    if token:
      cache.set(token_cache_key, token)

  if token:
    if token.last_used_time < datetime.now() - timedelta(hours=1):
      OAuthAccessToken.objects.filter(id=token.id).update(last_used_time=datetime.now())
      cache.delete(token_cache_key)

    user = User.get_cached(token.user_id)
    if not user:
      # User account was deleted.
      token.invalidate_cache()
      return None, None

    return user, token.scope

  return None, None


def invalidate_client_token(client_id, raw_token):
  access_tokens = OAuthAccessToken.objects.filter(client_id=client_id, token=raw_token,
      expire_time__isnull=True).order_by('-create_time')[:1]
  if access_tokens:
    OAuthAccessToken.objects.filter(id=access_tokens[0].id).update(expire_time=datetime.now())
    token_cache_key = CACHE_KEY_FORMAT % raw_token
    cache.delete(token_cache_key)
    return True

  return False


def invalidate_tokens_for_user(user):
  access_tokens = OAuthAccessToken.objects.filter(user=user,
      expire_time__isnull=True).order_by('-create_time')
  for access_token in access_tokens:
    OAuthAccessToken.objects.filter(id=access_token.id).update(expire_time=datetime.now())
    token_cache_key = CACHE_KEY_FORMAT % access_token.token
    cache.delete(token_cache_key)

