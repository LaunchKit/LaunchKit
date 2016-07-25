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

import base64
import hashlib
import logging
import json

from Crypto.Cipher import AES


ENCRYPTION_BLOCK_SIZE = 32


def encrypt_object(obj, secret):
  cipher = AES.new(secret)
  json_string = json.dumps(obj)
  padded = json_string + (ENCRYPTION_BLOCK_SIZE - len(json_string) % ENCRYPTION_BLOCK_SIZE) * ' '
  result = cipher.encrypt(padded)
  md5 = hashlib.md5(result).hexdigest()
  double_result = cipher.encrypt(result + md5)
  return base64.urlsafe_b64encode(double_result).rstrip('=')


def decrypt_object(obj, secret):
  try:
    # str() necessary here cuz utf8 kills b64decode
    str_obj = str(obj)
    encrypted = base64.urlsafe_b64decode(str_obj + (4 - len(str_obj) % 4) * '=')
  except TypeError:
    # Raised if b64 is invalid
    return None

  if not encrypted or len(encrypted) < 32:
    return None

  cipher = AES.new(secret)
  try:
    combo_string = cipher.decrypt(encrypted)
    md5 = combo_string[-32:]
    encrypted_json = combo_string[:-32]
    json_string = cipher.decrypt(encrypted_json)
  except ValueError:
    return None

  real_md5 = hashlib.md5(encrypted_json).hexdigest()
  if md5 != real_md5:
    logging.warn('Tampered encrypted string!')
    return None

  return json.loads(json_string)
