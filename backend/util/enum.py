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

import string


class Enum(object):
  __kinds__ = None

  @classmethod
  def keys(cls):
    for key in cls.__dict__:
      if key[0] in string.uppercase:
        yield key

  @classmethod
  def kinds(cls):
    if cls.__kinds__ is None:
      cls.__kinds__ = tuple([getattr(cls, key) for key in cls.keys()])
    return cls.__kinds__

  @classmethod
  def choices(cls):
    options = []
    for k in cls.keys():
      value = getattr(cls, k)
      title_parts = k.split('_')
      title_parts = [t[0] + t[1:].lower() for t in title_parts]
      options.append((value, ' '.join(title_parts),))
    return options