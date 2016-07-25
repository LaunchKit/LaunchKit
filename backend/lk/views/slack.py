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

from backend.lk.logic import appstore_review_subscriptions
from backend.lk.logic import appstore_sales_report_subscriptions
from backend.lk.logic import slack
from backend.lk.views.base import api_response
from backend.lk.views.base import api_user_view
from backend.lk.views.base import bad_request
from backend.lk.views.base import ok_response


@api_user_view('POST')
def connect_slack_view(request):
  code = request.POST.get('code')
  service = request.POST.get('service')
  onboarding = request.POST.get('onboarding') == '1'
  if not (code and service):
    return bad_request('Please provide a `code` from the Slack OAuth2 endpoint, LK `service` to connect, and `onboarding` status.')

  success = slack.associate_user_with_slack(request.user, code, service, onboarding)
  if not success:
    return bad_request('Could not fetch a slack token with that `code`.')

  return ok_response()


@api_user_view('GET')
def slack_channels_view(request):
  connected = slack.user_has_slack_token(request.user)
  if not connected:
    return bad_request('Unauthorized -- please connect slack first.')

  channels = slack.list_channels_for_user(request.user)

  # channels being None here means that we could not list any channels,
  # so something is probably wrong with the slack access token.
  return api_response({
    'tokenValid': channels is not None,
    'channels': channels,
  })


@api_user_view('GET')
def slack_usage_view(request):
  connected = slack.user_has_slack_token(request.user)
  review_channels = appstore_review_subscriptions.subscribed_slack_channel_names(request.user)
  sales_channels = appstore_sales_report_subscriptions.subscribed_slack_channel_names(request.user)

  return api_response({
    'connected': connected,
    'channelsByProduct': {
      'reviews': review_channels,
      'sales': sales_channels,
    }
  })


@api_user_view('POST')
def slack_disconnect_view(request):
  slack.invalidate_tokens_for_user(request.user)
  appstore_review_subscriptions.invalidate_slack_channel_subscriptions(request.user)
  appstore_sales_report_subscriptions.invalidate_slack_channel_subscriptions(request.user)

  return ok_response()
