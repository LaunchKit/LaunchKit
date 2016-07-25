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

import importlib
import inspect
import os.path
import glob
import sys

this_module = sys.modules[__name__]

python_files = os.path.join(os.path.dirname(__file__), '*.py')
for py_file in glob.glob(python_files):
  module_name = os.path.basename(py_file).replace('.py', '')
  module = __import__(module_name, globals(), locals(), [])
  for attr in dir(module):
    obj = getattr(module, attr)
    if inspect.isclass(obj):
      # if this is a class we define
      if obj.__module__.endswith(module_name):
        setattr(this_module, attr, obj)

    elif not inspect.ismodule(obj) and attr.upper()[0] == attr[0]:
      # or a non-module uppercase variable
      setattr(this_module, attr, obj)
