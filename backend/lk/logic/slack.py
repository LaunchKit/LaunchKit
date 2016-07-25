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

import collections
import copy
import json
import logging
import math
import urllib
from datetime import datetime

from celery.exceptions import TimeoutError
from django.apps import apps as django_apps
from django.conf import settings

from backend.lk.models import SlackAccessToken
from backend.lk.logic import urlfetch
from backend.util import urlutil
from backend import celery_app


NOTIFY_SLACK = settings.IS_PRODUCTION


SuccessShouldRetry = collections.namedtuple('SuccessShouldRetry', ['success', 'should_retry'])
SUCCESS = SuccessShouldRetry(True, False)
TEMPORARY_FAILURE = SuccessShouldRetry(False, True)
PERMANENT_FAILURE = SuccessShouldRetry(False, False)


def escape(string):
  string = string.replace('&', '&amp;')
  string = string.replace('<', '&lt;')
  string = string.replace('>', '&gt;')
  return string


def _make_request(method, path, token=None, params=None):
  headers = {}
  body = None
  if method == 'POST' and params:
    headers['Content-Type'] = 'application/x-www-form-urlencoded'
    try:
      body = urllib.urlencode(params)
    except:
      logging.exception('Invalid slack postbody: %r', params)
      return None

  slack_url = 'https://slack.com/api/%s' % path
  if token:
    slack_url = urlutil.appendparams(slack_url, token=token)

  code, headers, data = urlfetch.send_request(slack_url, method=method, body=body, headers=headers)
  if code != 200:
    logging.warn('Slack error for URL: %s -- %s %s %s', slack_url, code, headers, data)
    return None

  return data


def user_has_slack_token(user):
  return SlackAccessToken.objects.filter(user_id=user.id, invalidated_time__isnull=True).count() > 0

def invalidate_tokens_for_user(user):
  SlackAccessToken.objects \
      .filter(user_id=user.id, invalidated_time__isnull=True) \
      .update(invalidated_time=datetime.now(), token=None)


def associate_user_with_slack(user, code, service, onboarding=False):
  redirect_uri = '%saccount/slack/finish/' % settings.SITE_URL
  redirect_uri += '?service=' + service
  if onboarding:
    redirect_uri += '&onboarding=1'

  response = _make_request('POST', 'oauth.access', params={
    'code': code,
    'client_id': settings.SLACK_CLIENT_ID,
    'client_secret': settings.SLACK_CLIENT_SECRET,
    'redirect_uri': redirect_uri
  })

  if not response:
    return False

  token = response.get('access_token')
  scope = response.get('scope')
  webhook = response.get('incoming_webhook')

  if not (token and scope):
    return False

  try:
    async_result = _associate_user_with_slack.delay(user.id, token, scope, webhook)
  except:
    logging.exception('Task queue unavailable')

  try:
    async_result.wait(timeout=10.0)
  except TimeoutError:
    logging.warn('Timed out waiting for slack response')
    return False
  except:
    logging.exception('Task queue error waiting for slack')
    return False

  return bool(async_result.result)


@celery_app.task(queue='slack')
def _associate_user_with_slack(user_id, token, scope, webhook):
  # TODO: Encrypt this token somehow!
  encrypted_token = token
  token_obj = SlackAccessToken(user_id=user_id, token=encrypted_token, scope=scope)
  if webhook:
    token_obj.webhook_url = webhook['url']
    token_obj.webhook_channel = webhook['channel'].lstrip('#')
    token_obj.webhook_config_url = webhook['configuration_url']
  token_obj.save()
  return True


def list_channels_for_user(user):
  access_tokens = list(SlackAccessToken.objects.filter(user_id=user.id, invalidated_time__isnull=True))
  if not access_tokens:
    return None

  webhook_tokens = [t for t in access_tokens if t.webhook_url]
  if webhook_tokens:
    return [{'name': t.webhook_channel, 'webhook': True}
            for t in webhook_tokens]

  try:
    async_result = _list_channels_for_user.delay(user.id)
  except:
    logging.exception('Task queue unavailable')

  try:
    async_result.wait(timeout=10.0)
  except TimeoutError:
    logging.warn('Timed out waiting for slack response')
    return None
  except:
    logging.exception('Task queue error waiting for slack')
    return None

  return async_result.result


def _channel_obj(c):
  return {
    'id': c['id'],
    'name': c['name'],
  }


@celery_app.task(queue='slack')
def _list_channels_for_user(user_id):
  token = (SlackAccessToken.objects
              .filter(user_id=user_id, invalidated_time__isnull=True, webhook_data__isnull=True)
              .order_by('-id')).first()
  if not token:
    return None

  decrypted_token = token.token
  channels_response = _make_request('GET', 'channels.list', token=decrypted_token)

  if not (channels_response and channels_response.get('ok')):
    return None

  return [_channel_obj(c) for c in channels_response['channels']]


def post_message_to_slack_subscription(subscription_obj, message_dict, force=False):
  if not (force or NOTIFY_SLACK):
    logging.info('Not posting to slack subscription %s: %s', subscription_obj.id, message_dict)
    return

  model_name = subscription_obj.__class__.__name__
  sub_id = subscription_obj.id
  _post_message_to_slack_subscription.delay(model_name, sub_id, message_dict)


MAX_SLACK_RETRIES = 5
@celery_app.task(queue='slack', max_retries=MAX_SLACK_RETRIES + 1)
def _post_message_to_slack_subscription(model_name, sub_id, message_dict):
  SubKlass = django_apps.get_model(app_label='lk', model_name=model_name)
  sub = SubKlass.objects.get(pk=sub_id)

  if sub.slack_url:
    # webhook
    success, should_retry = post_message_to_webhook(sub.slack_url, message_dict)

  else:
    # connected user
    success, should_retry = post_message_to_connected_user(sub.user_id, message_dict,
        channel_id=sub.slack_channel_id, channel_name=sub.slack_channel_name)

  if success:
    return

  retries = _post_message_to_slack_subscription.request.retries
  if should_retry and retries < MAX_SLACK_RETRIES:
    countdown_secs = 2.0 * math.pow(2, retries)
    raise _post_message_to_slack_subscription.retry(countdown=countdown_secs)

  if should_retry:
    logging.info('Temporary failure for slack retried too many times; disabling %s - %s', model_name, sub_id)
  else:
    logging.info('Permanent failure for slack sub; disabling %s - %s', model_name, sub_id)

  # subscription broken. remove/disconnect/notify.
  SubKlass.objects.filter(id=sub_id).update(enabled=False, invalidated_time=datetime.now())


def post_message_to_connected_user(user_id, message_dict, channel_id=None, channel_name=None):
  access_tokens = list(
      SlackAccessToken.objects.filter(user_id=user_id, invalidated_time__isnull=True)
  )

  # Short-circuit in the case of an access token that has a configured webhook.
  webhook_token = next((t for t in access_tokens if t.webhook_channel == channel_name), None)
  all_access_token = next((t for t in access_tokens if t.webhook_data is None), None)

  if not (webhook_token or all_access_token):
    # Somehow we have a subscription without a corresponding token.
    return PERMANENT_FAILURE

  if webhook_token:
    token_id = webhook_token.id
    result = post_message_to_webhook(webhook_token.webhook_url, message_dict)

  else:
    token_id = all_access_token.id
    decrypted_token = all_access_token.token

    result = post_message_to_channel_with_token(decrypted_token, message_dict,
        channel_id=channel_id, channel_name=channel_name)

  if result == PERMANENT_FAILURE:
    logging.info('Permanent failure for slack access token: %s; invalidating', token_id)
    token_qs = SlackAccessToken.objects.filter(id=token_id)
    token_qs.update(token=None, invalidated_time=datetime.now())

  return result


#
# MESSAGE DELIVERY
#


def post_message_to_channel_with_token(token, message_dict, channel_id=None, channel_name=None):
  message_dict = copy.copy(message_dict)

  if channel_id:
    # prefer this because it's less fungible than channel_name
    message_dict['channel'] = channel_id
  else:
    message_dict['channel'] = '#%s' % channel_name

  if 'attachments' in message_dict:
    # Wow, a JSON-formatted string inside this form-encoded postbody.
    attachments = message_dict['attachments']
    if attachments and len(attachments) > 22:
      logging.warn('Slack message (channel) has too many attachments: %d message: %r', len(attachments), message_dict.get('text'))
    message_dict['attachments'] = json.dumps(attachments)

  response = _make_request('POST', 'chat.postMessage', token=token, params=message_dict)

  if response:
    if response['ok']:
      return SUCCESS

    err = response['error']
    if err in ('channel_not_found', 'is_archived', 'not_in_channel'):
      # TODO(Taylor): just this subscription could be removed in this case; the
      # slack connection might still be good.
      logging.info('Channel not found-ish: %s', err)
      return PERMANENT_FAILURE

    elif err in ('token_revoked', 'invalid_auth', 'not_authed', 'account_inactive'):
      logging.info('Token revoked-ish: %s', err)
      return PERMANENT_FAILURE

  logging.error('Unknown response from slack channel: %s -- %s', channel_id or channel_name, response)
  # Unknown, so we should retry.
  return TEMPORARY_FAILURE


def post_message_to_webhook(slack_url, message_dict):
  attachments = message_dict.get('attachments')
  if attachments and len(attachments) > 22:
    logging.warn('Slack message (webhook) has too many attachments: %d message: %r', len(attachments), message_dict.get('text'))

  postbody = json.dumps(message_dict)
  code, headers, data = urlfetch.send_request(slack_url, method='POST', body=postbody, json_response=False, headers={
    'Content-Type': 'application/json',
  })

  if code == 200:
    # Yay! All done.
    return SUCCESS

  if code == 404:
    # invalid hook
    if data in ('No service', 'No active hooks', 'Team disabled'):
      # This webhook URL is no longer valid -- no need to retry.
      logging.info('Invalid webhook: %s', data)
      return PERMANENT_FAILURE

  if code not in (500, 503, 504, -1):
    logging.warn('Undelivered slack message, unknown response: %s -> %s %s', slack_url, code, data)

  return TEMPORARY_FAILURE

