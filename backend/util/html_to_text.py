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
import logging
from HTMLParser import HTMLParser


class HTMLRawFormatter(HTMLParser):
    def __init__(self):
      self.reset()
      self._parts = []
      self._tag_stack = []
      self._tag_attributes = []

    @property
    def tag(self):
      if self._tag_stack:
        return self._tag_stack[-1]
      return None
    def attr(self, attr):
      if self._tag_attributes:
        attrs = self._tag_attributes[-1]
        if attr in attrs:
          return attrs[attr]
      return None

    def handle_starttag(self, tag, attrs_tuple):
      self._tag_stack.append(tag)
      self._tag_attributes.append(dict(attrs_tuple))

      if tag in ('br', 'div', 'p', 'td', 'table'):
        self._add_line()

      elif tag == 'img':
        alt = self.attr('alt')
        if alt:
          self._add_part(' ( Image: %s ) ' % alt)

    def handle_endtag(self, tag):
      if self.tag == 'a':
        href = self.attr('href')
        if href:
          self._add_part(' [ Link: %s ] ' % href)

      self._tag_stack.pop()
      self._tag_attributes.pop()

    def handle_charref(self, charref):
      char = None
      if charref == '8217':
        char = "'"
      elif charref == '8226':
        char = "-"
      elif charref in ('8220', '8221'):
        char = '"'

      if char:
        self._add_part(char)

    def handle_entityref(self, entity):
      char = None
      if entity == 'nbsp':
        char = ' '
      elif entity == 'rsquo':
        char = "'"
      elif entity == 'bull':
        char = '*'
      elif entity == 'gt':
        char = '>'
      elif entity == 'lt':
        char = '<'
      elif entity in ('ldquo', 'quot', 'rdquo'):
        char = '"'
      elif entity in ('mdash', 'ndash'):
        char = '--'

      if char:
        self._add_part(char)

    def handle_data(self, content):
      if self.tag not in ('title', 'style', 'script', 'tr'):
        self._add_part(content)

    def _add_part(self, part):
      if isinstance(part, unicode):
        # Kill unicode objects before we join() them.
        part = part.encode('utf-8')
      part = re.sub(r'[ \n\r]+', ' ', part)
      self._parts.append(part)

    def _add_line(self):
      self._parts.append('\n')

    def get_data(self):
      return ''.join(self._parts).strip()


def plaintextify(html):
  stripper = HTMLRawFormatter()
  try:
    stripper.feed(html)
  except:
    logging.exception('Could not strip tags!')
  return stripper.get_data()

