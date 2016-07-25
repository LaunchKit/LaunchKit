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

import httplib
import mimetypes
import os.path


BOUNDARY = '----------5e787aa69b512799e20372db1865a802'


def post_multipart(host, path, file_dict):
  content_type, body = _encode_multipart_formdata(file_dict)

  req = httplib.HTTP(host)
  req.putrequest('POST', path)
  req.putheader('Host', host)
  req.putheader('Content-Type', content_type)
  req.putheader('Content-Length', str(len(body)))
  req.endheaders()
  req.send(body)

  errcode, errmsg, headers = req.getreply()
  return req.file.read()


def _get_content_type(filename):
  return mimetypes.guess_type(filename)[0] or 'application/octet-stream'


def _encode_multipart_formdata(file_dict):
  body_parts = []
  for key, filename in file_dict.items():
    body_parts.append('--' + BOUNDARY)
    body_parts.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (key, os.path.basename(filename)))
    body_parts.append('Content-Type: %s' % _get_content_type(filename))
    body_parts.append('')
    with open(filename) as f:
      body_parts.append(f.read())

  body_parts.append('--' + BOUNDARY + '--')
  body_parts.append('')

  content_type = 'multipart/form-data; boundary=%s' % BOUNDARY
  return content_type, '\r\n'.join(body_parts)
