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

import logging
import re
from collections import namedtuple
from datetime import datetime
from datetime import timedelta

from backend.lk.logic import runtime_config
from backend.lk.logic import sessions
from backend.lk.logic import tokens
from backend.lk.models import SDKApp
from backend.lk.views.base import api_view
from backend.lk.views.base import api_response
from backend.util import text


ITUNES_RATING_URL_FORMAT = 'itms-apps://itunes.apple.com/WebObjects/MZStore.woa/wa/viewContentsUserReviews?type=Purple+Software&id=%d'

IOS_SDK_USER_AGENT_RE = re.compile(r'LaunchKit iOS SDK (\d+(\.\d+)*(-\w+)?)')


class ClientCommand(object):
  def __init__(self, command, kwargs):
    self.command = command
    self.args = kwargs

  def to_dict(self):
    return {
      'command': self.command,
      'args': self.args,
    }

class ClientLogCommand(ClientCommand):
  ERROR = 'error'
  WARN = 'warn'
  INFO = 'info'

  def __init__(self, level, message):
    super(ClientLogCommand, self).__init__('log', {
      'level': level,
      'message': message,
    })

class ClientSetSessionCommand(ClientCommand):
  def __init__(self, name, value):
    super(ClientSetSessionCommand, self).__init__('set-session', {
      'name': name,
      'value': value,
    })


def _event_time_valid(event_time):
  return event_time > datetime.now() - timedelta(days=30) and event_time < datetime.now() + timedelta(minutes=10)

RawTap = namedtuple('RawTap', ['time', 'x', 'y', 'orient'])
RawScreen = namedtuple('RawScreen', ['start', 'end', 'name'])

INVALID_SCREENS_COMMAND = ClientLogCommand(ClientLogCommand.WARN, 'Invalid "screens" list provided.')
INVALID_SCREEN_COMMAND = ClientLogCommand(ClientLogCommand.WARN, 'Invalid screen object provided.')
INVALID_TAPS_COMMAND = ClientLogCommand(ClientLogCommand.WARN, 'Invalid "taps" list provided.')
INVALID_TAP_BATCHES_COMMAND = ClientLogCommand(ClientLogCommand.WARN, 'Invalid "tapBatches" list provided.')
DO_NOT_INCLUDE_TAPS_AND_BATCHES_COMMAND = ClientLogCommand(ClientLogCommand.WARN, 'Do not include "taps" and "tapBatches".')
INVALID_TAP_COMMAND = ClientLogCommand(ClientLogCommand.WARN, 'Invalid tap object provided.')


DEFAULT_USER_DICT = {
  'name': '',
  'uniqueId': '',
  'email': '',
  'firstVisit': 0,
  'stats': {
    'visits': 0,
    'days': 0,
  },
  'labels': [],
}


def _handle_set_user(session, remote_addr, post_data):
  unique_id = post_data.get('unique_id')
  name = post_data.get('name')
  email = post_data.get('email')

  sessions.set_user_info(session, remote_addr,
      unique_id=unique_id, name=name, email=email)

EVENT_TO_HANDLER = {
  'set-user': _handle_set_user,
}


def _filter_screens(raw_screens, commands):
  if not raw_screens:
    return []

  if not isinstance(raw_screens, list):
    commands.append(INVALID_SCREENS_COMMAND)
    return []

  filtered_screens = []
  for raw_screen in raw_screens:
    try:
      start = datetime.fromtimestamp(float(raw_screen.get('start', 0)))
      end = datetime.fromtimestamp(float(raw_screen.get('end', 0)))
      name = raw_screen.get('name') or '?'
    except (AttributeError, TypeError, ValueError, KeyError):
      commands.append(INVALID_SCREEN_COMMAND)
      continue

    any_invalid = not all(map(_event_time_valid, [start, end]))
    if end < start or any_invalid:
      logging.info('Invalid screen time (%s - %s) for session', start, end)
      commands.append(INVALID_SCREEN_COMMAND)
      continue

    filtered_screens.append(RawScreen(start, end, name))

  return filtered_screens


def _filter_tap(raw_tap, commands):
  if not isinstance(raw_tap, dict):
    commands.append(INVALID_TAP_COMMAND)
    return None

  try:
    x, y = float(raw_tap.get('x', -1)), float(raw_tap.get('y', -1))
    time = datetime.fromtimestamp(float(raw_tap.get('time', 0)))
    orient = raw_tap.get('orient', '?')
  except (AttributeError, TypeError, ValueError, KeyError):
    commands.append(INVALID_TAP_COMMAND)
    return None

  if not _event_time_valid(time):
    commands.append(INVALID_TAP_COMMAND)
    return None

  return RawTap(time, x, y, orient)


def _filter_tap_batches(tap_batches, commands):
  if not tap_batches:
    return []

  if not isinstance(tap_batches, list):
    commands.append(INVALID_TAP_BATCHES_COMMAND)
    return []

  raw_batch_taps = []
  for batch in tap_batches:
    if not isinstance(batch, dict):
      commands.append(INVALID_TAP_BATCHES_COMMAND)
      continue

    screen = batch.get('screen', {})
    if not isinstance(screen, dict):
      commands.append(INVALID_TAP_BATCHES_COMMAND)
      continue

    w, h = screen.get('w', 0), screen.get('h', 0)
    if not (isinstance(w, int) and isinstance(h, int)):
      commands.append(INVALID_TAP_BATCHES_COMMAND)
      continue

    batch_taps = batch.get('taps', [])
    if not isinstance(batch_taps, list):
      commands.append(INVALID_TAP_BATCHES_COMMAND)
      continue

    if w > h:
      orient = 'l'
    else:
      orient = 'p'

    for raw_tap in batch_taps:
      raw_tap['orient'] = orient
      filtered_tap = _filter_tap(raw_tap, commands)
      if filtered_tap:
        raw_batch_taps.append(filtered_tap)

  return raw_batch_taps


def _filter_taps(raw_taps, commands):
  if not raw_taps:
    return []

  if not isinstance(raw_taps, list):
    commands.append(INVALID_TAP_COMMAND)
    return []

  filtered_taps = []
  for raw_tap in raw_taps:
    filtered_tap = _filter_tap(raw_tap, commands)
    if filtered_tap:
      filtered_taps.append(filtered_tap)
  return filtered_taps


@api_view('POST')
def track_view(request):
  config = {}
  commands = []
  sdk_user = None

  def response():
    return api_response({
      'do': [c.to_dict() for c in commands],
      'config': config,
      'user': (sdk_user and sdk_user.to_client_dict()) or DEFAULT_USER_DICT,
    })

  post_data = request.DATA or {}
  bundle_id = post_data.get('bundle') or post_data.get('bundle_id')
  # TODO(Taylor): Validation.
  version = post_data.get('version')
  build = post_data.get('build')
  debug = post_data.get('debug_build') == '1'

  os_name = None
  os_version = post_data.get('os_version')
  if os_version:
    os_name, os_version = os_version.split(' ', 1)

  now = datetime.now()
  token = post_data.get('token')
  if isinstance(token, basestring):
    user = tokens.user_by_token(token)
  else:
    user = None

  if not user:
    if token:
      log_message = 'Invalid `token`, please use the website to generate a token for your account.'
    else:
      log_message = 'Please ensure "token" is set before calling /track.'
    commands.append(ClientLogCommand(ClientLogCommand.ERROR, log_message))
    return response()

  if not user.flags.has_sent_tracking_data:
    user.set_flags(['has_sent_tracking_data'])

  session_data = post_data.get('session', {})
  session_id = session_data.get('session_id')

  session = None
  if session_id:
    session = sessions.get_session_by_encrypted_id(user, session_id)

  if not session:
    if not bundle_id:
      commands.append(ClientLogCommand(ClientLogCommand.ERROR, 'Invalid "bundle", please provide a bundle.'))
      return response()

    session = sessions.create_session(user, bundle_id)
    commands.append(ClientSetSessionCommand('session_id', session.encrypted_id))

  elif bundle_id and session.app.bundle_id != bundle_id:
    logging.warn('Invalid session_id for bundle: %s', bundle_id)
    commands.append(ClientLogCommand(ClientLogCommand.ERROR, 'Invalid "session_id" for bundle: %s' % bundle_id))
    return response()

  app = session.app
  track_time = app.latest_track_time
  if not track_time or track_time < now - timedelta(minutes=5):
    SDKApp.objects.filter(id=app.id).update(latest_track_time=now)

  if version:
    if debug:
      if not app.latest_debug_version or text.cmp_version(app.latest_debug_version, version) < 0:
        SDKApp.objects.filter(id=app.id).update(latest_debug_version=version)
    else:
      if not app.latest_prod_version or text.cmp_version(app.latest_prod_version, version) < 0:
        SDKApp.objects.filter(id=app.id).update(latest_prod_version=version)

  screen = post_data.get('screen', {})
  screen_width = screen.get('width')
  screen_height = screen.get('height')
  screen_scale = screen.get('scale')

  hardware = post_data.get('hardware')

  user_agent = request.META.get('HTTP_USER_AGENT', '')
  sdk_platform = None
  sdk_version = None
  ios_sdk_match = IOS_SDK_USER_AGENT_RE.search(user_agent)
  if ios_sdk_match:
    sdk_platform = 'iOS'
    sdk_version = ios_sdk_match.group(1)

  sessions.update_attributes(session, request.remote_addr,
    version=version,
    build=build,
    debug=debug,
    os=os_name,
    os_version=os_version,
    hardware=hardware,
    screen_width=screen_width,
    screen_height=screen_height,
    screen_scale=screen_scale,
    sdk_platform=sdk_platform,
    sdk_version=sdk_version)

  track_command = post_data.get('command', 'track')
  handler = EVENT_TO_HANDLER.get(track_command)
  if handler:
    handler(session, request.remote_addr, post_data)

  elif track_command != 'track':
    commands.append(ClientLogCommand(ClientLogCommand.WARN, 'Unknown "command" provided.'))

  # ACTUAL TRACKING BEGINS

  filtered_screens = _filter_screens(post_data.get('screens'), commands)

  batches = post_data.get('tapBatches')
  if batches:
    filtered_taps = _filter_tap_batches(batches, commands)
  else:
    filtered_taps = _filter_taps(post_data.get('taps'), commands)

  sessions.track(session, track_command, raw_taps=filtered_taps, raw_screens=filtered_screens)

  # This sets config above and is included in the response.
  config = runtime_config.interpolated_config_for_session(session)

  if session.last_upgrade_time:
    config['io.launchkit.currentVersionDuration'] = (now - session.last_upgrade_time).total_seconds()
  config['io.launchkit.installDuration'] = (now - session.create_time).total_seconds()

  # Set this for the response.
  sdk_user = session.sdk_user

  return response()
