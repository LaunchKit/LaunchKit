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

import time

from django.core.cache import cache
from django.db import models

from backend.util import cryptoid


POSTGRES_MAX_INT = 2147483647


class APIModel(models.Model):
  class Meta:
    abstract = True
    app_label = 'lk'

  #
  # ENCRYPTED IDS
  #
  @property
  def encrypted_id(self):
    return self.__class__.encrypt_id(self.id)

  @classmethod
  def encrypt_id(cls, raw_id):
    # pylint: disable=E1101
    return cryptoid.encrypt_id(raw_id, key_token=cls.ENCRYPTED_ID_KEY_TOKEN)
  @classmethod
  def decrypt_id(cls, encrypted_id):
    # pylint: disable=E1101
    maybe_id = cryptoid.decrypt_id(encrypted_id, key_token=cls.ENCRYPTED_ID_KEY_TOKEN)
    # IMPORTANT: Ids that are too large to be represented as integers in postgres
    # result in a filtering seq scan of entire table rather than index lookup,
    # so prevent them from making it that far.
    if maybe_id > POSTGRES_MAX_INT:
      return None
    return maybe_id

  @classmethod
  def find_by_encrypted_id(cls, encrypted_id, **kwargs):
    instances = cls.find_by_encrypted_ids([encrypted_id], **kwargs)
    # might be [None] if this is not found.
    return instances[0]

  @classmethod
  def find_by_encrypted_ids(cls, encrypted_ids, for_update=False, **filter_params):
    raw_ids = []
    for encrypted_id in encrypted_ids:
      raw_id = cls.decrypt_id(encrypted_id)
      if raw_id:
        raw_ids.append(raw_id)

    qs = cls.objects.filter(id__in=raw_ids, **filter_params)
    if for_update:
      qs = qs.select_for_update()

    instances_by_id = {i.encrypted_id: i for i in qs}
    return [instances_by_id.get(eid) for eid in encrypted_ids]

  #
  # CACHING
  #

  @classmethod
  def get_cached(cls, an_id):
    # pylint: disable=E1101
    key = cls.cache_key_for_id(an_id)
    obj = cache.get(key)
    if not obj:
      try:
        obj = cls.objects.get(pk=an_id)
        cache.set(key, obj)
      except cls.DoesNotExist:
        obj = None
    return obj

  @classmethod
  def get_multi_cached(cls, ids):
    # pylint: disable=E1101
    key_to_id = dict((cls.cache_key_for_id(an_id), an_id) for an_id in ids)
    all_keys = key_to_id.keys()
    cached_objs_by_key = cache.get_many(all_keys)

    objects_by_id = {}
    ids_to_fetch = []
    for key in all_keys:
      if key in cached_objs_by_key:
        obj = cached_objs_by_key[key]
        objects_by_id[obj.id] = obj
      else:
        ids_to_fetch.append(key_to_id[key])

    if ids_to_fetch:
      for obj in cls.objects.filter(id__in=ids_to_fetch):
        objects_by_id[obj.id] = obj
        key = cls.cache_key_for_id(obj.id)
        cache.set(key, obj)

    return [objects_by_id.get(an_id) for an_id in ids]

  @property
  def cache_key(self):
    # pylint: disable=E1101
    return self.__class__.cache_key_for_id(self.id)

  def save(self, *args, **kwargs):
    value = super(APIModel, self).save(*args, **kwargs)
    self.invalidate_cache()
    return value

  def delete(self, *args, **kwargs):
    self.invalidate_cache()
    value = super(APIModel, self).delete(*args, **kwargs)
    return value

  def invalidate_cache(self):
    if hasattr(self, 'cache_key_for_id'):
      cache.delete(self.cache_key)

  def to_qs(self):
    return self.__class__.objects.filter(id=self.id)

  #
  # MISC
  #

  @classmethod
  def date_to_api_date(self, date):
    if not date:
      return None
    timestamp = time.mktime(date.timetuple())
    if hasattr(date, 'microsecond'):
      # datetime.date objects have no microsecond.
      timestamp += (date.microsecond / 1000000.0)
    return timestamp
