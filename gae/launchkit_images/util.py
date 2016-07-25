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

from third_party.poster.encode import MultipartParam
from third_party.poster.encode import multipart_encode


def encode_multipart_formdata(fields, files):
    """
    fields is a sequence of (name, value) elements for regular form fields.
    files is a sequence of (name, filename, value) elements for data to be uploaded as files
    Return (content_type, body) ready for httplib.HTTP instance
    """
    multipart_items = [(k, (v or '')) for k, v in fields.items()]
    for (key, (filename, content_type, value,)) in files.iteritems():
        item = MultipartParam(key, value=value, filename=filename, filetype=content_type)
        multipart_items.append(item)

    datagen, headers = multipart_encode(multipart_items)
    body = ''.join(datagen)
    return headers, body
