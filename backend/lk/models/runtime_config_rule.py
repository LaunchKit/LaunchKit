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

from django.db import models

from backend.lk.models.apimodel import APIModel
from backend.lk.models.users import User
from backend.util import enum
from backend.util import hstore_field



class ConfigKind(enum.Enum):
  STRING = 'string'
  INT = 'int'
  FLOAT = 'float'
  BOOL = 'bool'


class MatchOperator(enum.Enum):
  GREATER_OR_EQUAL = 'gte'
  GREATER = 'gt'
  EQUAL = 'eq'
  LESS_OR_EQUAL = 'lte'
  LESS = 'lt'


class RuntimeConfigRule(APIModel):
  ENCRYPTED_ID_KEY_TOKEN = 'cloudconfiggintool'

  user = models.ForeignKey(User, related_name='+', on_delete=models.DO_NOTHING)
  create_time = models.DateTimeField(auto_now_add=True)
  sort_time = models.DateTimeField(auto_now_add=True)
  update_time = models.DateTimeField(auto_now=True, null=True)

  key = models.CharField(max_length=64)
  kind = models.CharField(max_length=8, choices=ConfigKind.choices())
  namespace = models.CharField(max_length=16, null=True)
  bundle_id = models.CharField(max_length=256, null=False)

  value = models.CharField(max_length=2048)
  description = models.CharField(max_length=2048, null=True)

  qualifiers = hstore_field.HStoreField(null=True)

  version = qualifiers.string_property()
  version_match = qualifiers.string_property()
  build = qualifiers.string_property()
  build_match = qualifiers.string_property()
  ios_version = qualifiers.string_property()
  ios_version_match = qualifiers.string_property()
  debug = qualifiers.bool_property()
  sdk_user_labels = qualifiers.string_property()

  @property
  def specificity(self):
    s = len(self.qualifiers or {})

    if self.version_match == MatchOperator.EQUAL:
      s += 1
    if self.build_match == MatchOperator.EQUAL:
      s += 1
    if self.ios_version_match == MatchOperator.EQUAL:
      s += 1

    return s

  @property
  def typed_value(self):
    if self.kind == ConfigKind.INT:
      return int(self.value)
    if self.kind == ConfigKind.FLOAT:
      return float(self.value)
    if self.kind == ConfigKind.BOOL:
      return self.value == '1'
    return self.value

  def set_typed_value(self, value):
    if self.kind == ConfigKind.INT:
      self.value = '%s' % value
    elif self.kind == ConfigKind.FLOAT:
      self.value = repr(value)
    elif self.kind == ConfigKind.BOOL:
      self.value = '%s' % int(value)
    else:
      self.value = value

  def to_dict(self):
    result = {
      'id': self.encrypted_id,
      'key': self.key,
      'kind': self.kind,
      'description': self.description,

      'createTime': self.date_to_api_date(self.create_time),
      'sortTime': self.date_to_api_date(self.sort_time),
      'updateTime': self.date_to_api_date(self.update_time),

      'value': self.typed_value,
    }
    if self.bundle_id:
      result['bundleId'] = self.bundle_id
    if self.version:
      result['version'] = self.version
    if self.version_match:
      result['versionMatch'] = self.version_match
    if self.build:
      result['build'] = self.build
    if self.build_match:
      result['buildMatch'] = self.build_match
    if self.ios_version:
      result['iosVersion'] = self.ios_version
    if self.ios_version_match:
      result['iosVersionMatch'] = self.ios_version_match
    return result


class RuntimeConfigRuleNamespace(APIModel):
  class Meta:
    unique_together = ('user', 'bundle_id', 'namespace')
    app_label = 'lk'

  user = models.ForeignKey(User, related_name='+', on_delete=models.DO_NOTHING)
  update_time = models.DateTimeField(auto_now_add=True, auto_now=True, null=True)

  bundle_id = models.CharField(max_length=256, null=True)
  namespace = models.CharField(max_length=16, null=True)

  def to_dict(self):
    return {
      'updateTime': self.date_to_api_date(self.update_time),

      'bundleId': self.bundle_id,
      'namespace': self.namespace
    }
