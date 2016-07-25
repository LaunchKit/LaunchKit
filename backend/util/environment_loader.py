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

import glob
import json
import os
import types


class EnvironmentLoaderError(RuntimeError):
  pass


class Environment(object):
  def __init__(self, name, env_dict):
    self.name = name
    self._env_dict = env_dict
    self._module = None
  def keys(self):
    return self._env_dict.keys()
  def get_module(self):
    if not self._module:
      self._module = types.ModuleType(self.name)
      self.annotate_module(self._module)
    return self._module
  def annotate_module(self, module):
    for k,v in self._env_dict.items():
      setattr(module, k, v)


def load_environments(basedir, default='default', source_replace_dict=None):
  json_files = {}

  for filename in glob.glob(os.path.join(basedir, '*.json')):
    env = os.path.splitext(os.path.basename(filename))[0]
    with file(filename, 'r') as json_file:
      content = json_file.read()
      if source_replace_dict:
        for k, v in source_replace_dict.items():
          content = content.replace(k, v)
      try:
        json_files[env] = json.loads(content)
      except ValueError as e:
        raise EnvironmentLoaderError('Cannot parse %s.json! %r' % (env, e))

  if default not in json_files:
    raise EnvironmentLoaderError('Cannot find default %s! Choices: %s' % (default, json_files.keys()))

  default_dict = json_files[default]

  environments = {}
  for environment_name, env_specific_dict in json_files.items():
    merged_dict = default_dict.copy()
    for setting in default_dict.keys():
      if setting in env_specific_dict:
        merged_dict[setting] = env_specific_dict[setting]

    environments[environment_name] = Environment(environment_name, merged_dict)

  return environments
