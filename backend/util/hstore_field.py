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
from datetime import datetime

from django.db import models
from sqlalchemy.dialects.postgresql.hstore import _parse_hstore, _serialize_hstore



def from_hstore_str(value):
  if isinstance(value, unicode):
    return value
  if isinstance(value, str):
    return unicode(value, 'utf-8')
  return unicode(value)

def to_hstore_str(value):
  if not isinstance(value, basestring):
    value = str(value)
  return value


def bool_from_hstore_str(value):
  if value in ('1', 'True'):
    return True
  return False

def bool_to_hstore_str(value):
  if value:
    return '1'
  else:
    return '0'


def datetime_from_hstore_str(value):
  if value:
    timestamp = float(value)
    return datetime.fromtimestamp(timestamp)
  return None

def datetime_to_hstore_str(dt):
  timestamp = time.mktime(dt.timetuple())
  if hasattr(dt, 'microsecond'):
    # datetime.date objects have no microsecond.
    timestamp += (dt.microsecond / 1000000.0)
  return '%0.6f' % timestamp


class HStoreField(models.TextField):
  __metaclass__ = models.SubfieldBase

  def __init__(self, *args, **kwargs):
    super(HStoreField, self).__init__(*args, **kwargs)

  def to_python(self, value):
    if value is None:
      return None
    if isinstance(value, dict):
      return value
    value = _parse_hstore(value)
    # _parse_hstore doesn't handle unicode properly.
    return dict((k, v and unicode(v, 'utf-8')) for k, v in value.items())

  def get_db_prep_save(self, value, connection):
    if value is None:
      return None
    if isinstance(value, str):
      return value
    return _serialize_hstore(value)

  def db_type(self, connection):
    return 'hstore'

  def _typed_property(self, dict_key=None, from_hstore_string_fn=from_hstore_str, to_hstore_string_fn=to_hstore_str):
    return HStoreProperty(self, dict_key=dict_key, from_hstore_string_fn=from_hstore_string_fn, to_hstore_string_fn=to_hstore_string_fn)

  def string_property(self, dict_key=None):
    return self._typed_property(dict_key=dict_key)

  def int_property(self, dict_key=None):
    return self._typed_property(dict_key=dict_key, from_hstore_string_fn=int)

  def long_property(self, dict_key=None):
    return self._typed_property(dict_key=dict_key, from_hstore_string_fn=long)

  def float_property(self, dict_key=None):
    return self._typed_property(dict_key=dict_key, from_hstore_string_fn=float)

  def bool_property(self, dict_key=None):
    return self._typed_property(dict_key=dict_key, from_hstore_string_fn=bool_from_hstore_str,
        to_hstore_string_fn=bool_to_hstore_str)

  def datetime_property(self, dict_key=None):
    return self._typed_property(dict_key=dict_key, from_hstore_string_fn=datetime_from_hstore_str,
        to_hstore_string_fn=datetime_to_hstore_str)



class HStoreProperty(object):
  def __init__(self, hstore_field, from_hstore_string_fn=from_hstore_str, to_hstore_string_fn=to_hstore_str, dict_key=None):
    self._hstore_field = hstore_field
    self._from_hstore_string_fn = from_hstore_string_fn
    self._to_hstore_string_fn = to_hstore_string_fn
    self._dict_key = dict_key
    self._class_attr_name = None

  def _name_on_class(self, obj):
    if not self._class_attr_name:
      for k, v in obj.__class__.__dict__.items():
        if v == self:
          self._class_attr_name = k
          break
    return self._class_attr_name

  def __get__(self, obj, objtype=None):
    if obj is None:
      return self
    dict_key = self._dict_key or self._name_on_class(obj)
    data = getattr(obj, self._hstore_field.name)
    if not data or dict_key not in data:
      return None
    value = data[dict_key]
    return self._from_hstore_string_fn(value)

  def __set__(self, obj, value):
    dict_key = self._dict_key or self._name_on_class(obj)
    data = getattr(obj, self._hstore_field.name)
    if not data:
      data = {}
      setattr(obj, self._hstore_field.name, data)
    if value is None:
      if dict_key in data:
        del data[dict_key]
    else:
      data[dict_key] = self._to_hstore_string_fn(value)
