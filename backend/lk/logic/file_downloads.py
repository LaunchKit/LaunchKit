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

import tempfile
from contextlib import contextmanager

import requests


@contextmanager
def download_file(url, prefix='lk'):
  r = requests.get(url, stream=True)

  if r.status_code != 200:
    yield r.status_code, None
    return

  content_type = r.headers.get('content-type') or ''
  if 'jpg' in content_type or 'jpeg' in content_type:
    extension = '.jpg'
  elif 'gif' in content_type:
    extension = '.gif'
  elif 'png' in content_type:
    extension = '.png'
  elif 'mp4' in content_type:
    extension = '.mp4'
  else:
    extension = ''

  with tempfile.NamedTemporaryFile(prefix=prefix, suffix=extension) as f:
    for chunk in r.iter_content(1024):
      f.write(chunk)
    f.flush()
    yield 200, f.name
