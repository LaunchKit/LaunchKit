# encoding: utf-8
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

import re
import string

from Crypto.Random import random


# Random: length of a twitter t.co URL.
TCO_URL_LENGTH = 23


TOKEN_SOURCE = string.lowercase + string.uppercase + string.digits + '-_'
def random_urlsafe_token(length=32):
  """Generates a random URL-safe string of a given length."""
  return ''.join(random.choice(TOKEN_SOURCE) for i in range(length))


HUMAN_TOKEN_SOURCE = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
def random_humanized_token(length):
  """Generates a random string of a given length, suitable for reading by
  humans.
  """
  return ''.join(random.choice(HUMAN_TOKEN_SOURCE) for i in range(length))


def random_numeric_token(length):
  """Generates a random string of a given length, suitable for typing on a numeric keypad.
  """
  return ''.join(random.choice(string.digits) for i in range(length))


VALID_FILENAME_CHARS = set("-_.()#'\" %s%s" % (string.ascii_letters, string.digits))
def filename(s):
  return (''.join(c for c in s if c in VALID_FILENAME_CHARS)).strip() or ''


def app_short_name(app_name):
  """For a given long-format name from the App Store, return just a short name for the app.

  >>> app_short_name('Cluster - share moments')
  'Cluster'
  >>> app_short_name(u'Cluster \u2013 share moments')
  u'Cluster'
  >>> app_short_name('Cluster: private moments')
  'Cluster'
  >>> app_short_name('Cluster')
  'Cluster'
  >>> app_short_name('Cluster This Name Is Too Long Dontcha Think')
  'Cluster This Name Is Too Long...'
  """
  name, _ = app_name_tagline(app_name)
  if len(name) > 32:
    return name[:29].strip() + '...'
  return name


def app_name_tagline(app_name):
  """Splits app name into app name and tagline given common formats of app names.

  >>> app_name_tagline('Cluster - share moments')
  ('Cluster', 'share moments')
  >>> app_name_tagline('Cluster')
  ('Cluster', '')
  >>> app_name_tagline('Cluster: Privates')
  ('Cluster', 'Privates')
  """
  name_parts = [p for p in re.split(ur'(?: [|–—-]+ |: )', app_name) if p]
  app_name = name_parts[0].strip()
  app_tagline = ''
  if len(name_parts) > 1:
    app_tagline = name_parts[1]

  return app_name, app_tagline


def ellipsize_bytes(full_text, bytes):
  if not full_text:
    return full_text

  trimmed_text = full_text[:bytes]
  while len(trimmed_text.encode('utf8', 'replace')) > bytes:
    # TODO(taylor): Implement binary search.
    trimmed_text = trimmed_text[:-1]

  if trimmed_text != full_text:
    trimmed_text += ' ...'

  return trimmed_text

NON_NUMERIC_RE = re.compile(r'[^\d]+')

def _version_string_to_int_array(version):
  if not version:
    return []
  # Strip away '-alpha1' on the end.
  primary_version = version.split('-')[0]
  return [int(part) for part in NON_NUMERIC_RE.split(primary_version) if part]

def cmp_version(version, other_version):
  """Tests two version strings to see if one is newer. Ignores 1.0-trailing1 sub-versions.

  >>> cmp_version('1.0', '1.0')
  0
  >>> cmp_version('1.0', '1.1')
  -1
  >>> cmp_version('1.0', '0.9')
  1
  >>> cmp_version('1.0', '0.9.1')
  1
  >>> cmp_version('1', '1.0.0.0.1')
  -1
  >>> cmp_version('1.0-alpha1', '1.0')
  0
  >>> cmp_version('1.0-alpha1', '1.0-alpha2')
  0
  >>> cmp_version('1.0.', '1.0')
  0
  """
  parts = _version_string_to_int_array(version)
  other_parts = _version_string_to_int_array(other_version)
  # Zero-pad the tuples so they're the same length.
  len_diff = len(parts) - len(other_parts)
  if len_diff < 0:
    parts += [0] * (-1 * len_diff)
  else:
    other_parts += [0] * len_diff
  return cmp(parts, other_parts)

def cmp_build(build, other_build):
  if build and not other_build:
    return 1
  if other_build and not build:
    return -1

  try:
    build = int(build)
    other_build = int(other_build)
  except ValueError:
    pass

  if build > other_build:
    return 1
  if other_build > build:
    return -1
  return 0


def english_join(items):
  if len(items) == 1:
    items_text = items[0]
  elif len(items) < 5:
    items_text = ', '.join(items[:-1])
    items_text += ' and %s' % items[-1]
  else:
    items_text = ', '.join(items[:3])
    items_text += ' and %d more' % (len(items) - 3)
  return items_text
