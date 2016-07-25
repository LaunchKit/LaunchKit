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
import struct

from Crypto.Cipher import DES
from django.conf import settings


BASE_KEY = settings.ENCRYPTED_ID_KEY_IV[:8]
BASE_IV = settings.ENCRYPTED_ID_KEY_IV[8:16]


KEY_IV_BY_TOKEN = {}
def key_iv_for_token(token):
  if token not in KEY_IV_BY_TOKEN:
    key, iv = bytearray(BASE_KEY), bytearray(BASE_IV)
    if token:
      token_bytes = bytearray(token)
      for i in range(len(token)):
        key[i % 8] = (key[i % 8] + token_bytes[i]) % 256
        iv[i % 8] = (iv[i % 8] + token_bytes[i]) % 256
    KEY_IV_BY_TOKEN[token] = (str(key), str(iv))

  return KEY_IV_BY_TOKEN[token]


def encrypt_id(raw_id, key_token=None):
  if not raw_id or not isinstance(raw_id, int) or raw_id < 1:
    raise TypeError('Invalid ID to encrypt: %r' % raw_id)

  key, iv = key_iv_for_token(key_token)
  eng = DES.new(key, DES.MODE_CBC, iv)
  result = eng.encrypt(struct.pack('<Q', raw_id))
  return base64.urlsafe_b64encode(result).rstrip('=')


def decrypt_id(encrypted_id, key_token=None):
  if not encrypted_id or not len(encrypted_id) == 11:
    return None

  try:
    # str() necessary here cuz utf8 kills b64decode
    encrypted = base64.urlsafe_b64decode(str(encrypted_id) + '=')
  except TypeError:
    # Raised if b64 is invalid
    return None

  key, iv = key_iv_for_token(key_token)
  eng = DES.new(key, DES.MODE_CBC, iv)

  decrypted = eng.decrypt(encrypted)
  return struct.unpack('<Q', decrypted)[0]


