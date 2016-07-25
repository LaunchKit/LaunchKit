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
import urlparse
from datetime import datetime
from datetime import date


from django import forms
from django.core import validators

from backend.lk.models import APIModel
from backend.lk.models import ItunesConnectVendor
from backend.lk.logic import appstore_sales_report_subscriptions
from backend.lk.logic import destructive
from backend.lk.logic import itunes_connect
from backend.lk.views.base import api_response
from backend.lk.views.base import api_user_view
from backend.lk.views.base import api_view
from backend.lk.views.base import bad_request
from backend.lk.views.base import not_found
from backend.lk.views.base import ok_response
from backend.lk.views.base import unavailable_response
from backend.util import lkforms


class NewSubscriptionForm(forms.Form):
  email = lkforms.LKEmailField(required=False)
  my_email = lkforms.LKBooleanField(required=False)

  slack_channel_name = forms.CharField(required=False, max_length=128)
  slack_url = forms.URLField(required=False)

  def clean_slack_url(self):
    slack_url = self.cleaned_data.get('slack_url')
    if slack_url:
      if urlparse.urlparse(slack_url).netloc != 'hooks.slack.com' or '/services/' not in slack_url:
        raise forms.ValidationError('Slack URL should be a hooks.slack.com URL and start with /services/.')
    return slack_url

  def clean(self):
    email = self.cleaned_data.get('email')
    my_email = self.cleaned_data.get('my_email', False)
    slack_url = self.cleaned_data.get('slack_url')
    slack_channel_name = self.cleaned_data.get('slack_channel_name', False)

    # the form is considered legit if it contains just one of the parameters for creating a sales report subsciption
    legit = len(filter(lambda x: x, [email, my_email, slack_channel_name, slack_url])) == 1

    if not legit:
      raise forms.ValidationError('Please provide `email` or `my_email` or `slack_url` or `slack_channel`, but just one.')

    return self.cleaned_data


@api_user_view('POST')
def connect_itunes_view(request):
  apple_id = request.POST.get('apple_id', '').strip()
  password = request.POST.get('password', '')
  if not (apple_id and password):
    return bad_request('Please provide an Apple ID and password.', errors={'kind': 'auth'})

  vendors_response = itunes_connect.associate_user_with_itunes_connect(request.user, apple_id, password)
  if not vendors_response:
    # task queue down, etc.
    return unavailable_response()

  if vendors_response.auth_error:
    return bad_request('Could not authenticate with iTunes Connect.', errors={'__all__': vendors_response.auth_error, 'kind': 'auth'})
  elif vendors_response.vendors_error:
    return bad_request('Could not fetch iTunes Connect vendors.', errors={'__all__': vendors_response.vendors_error, 'kind': 'vendors'})
  elif vendors_response.connection_error:
    return bad_request('Could not talk to iTunes Connect.', errors={'__all__': vendors_response.connection_error, 'kind': 'connection'})
  elif not vendors_response.vendors:
    return bad_request('No vendors associated with this account.', errors={'__all__': 'No vendors associated with account', 'kind': 'vendors'})

  return ok_response()


@api_user_view('GET')
def get_vendors_view(request):
  connected_email = itunes_connect.itunes_credentials_email_for_user_id(request.user.id)
  vendors = ItunesConnectVendor.objects.filter(user=request.user)
  return api_response({
    'appleId': connected_email,
    'vendors': [vendor.to_dict() for vendor in vendors]
  })


@api_user_view('POST')
def disconnect_itunes_view(request):
  connected_email = itunes_connect.itunes_credentials_email_for_user_id(request.user.id)
  if not connected_email:
    return bad_request('No connection to remove.')

  destructive.delete_itunes_connection_and_imports(request.user)

  return ok_response()


@api_user_view('POST')
def choose_vendor_view(request):
  vendor_id = request.POST.get('vendor_id')
  if not vendor_id:
    return bad_request()

  vendor = ItunesConnectVendor.find_by_encrypted_id(vendor_id)
  if not vendor or vendor.user_id != request.user.id:
    return bad_request()

  itunes_connect.choose_vendor(request.user, vendor)

  return ok_response()


@api_user_view('GET')
def get_sales_metrics_view(request):
  requested_date = request.GET.get('requested_date')
  if requested_date:
    try:
      requested_date = float(requested_date)
      requested_date = date.fromtimestamp(requested_date)
    except ValueError:
      return bad_request('Invalid `requsted_date`')

  if not requested_date:
    requested_date = itunes_connect.get_freshest_sales_report_date()

  vendor = itunes_connect.get_chosen_vendor_for_user(request.user)
  if not vendor:
    return bad_request('No iTunes vendor chosen for this user yet.')

  status = itunes_connect.report_status_for_vendor_date(vendor, requested_date)
  if status == itunes_connect.REPORT_STATUS_AVAILABLE:
    app_sales_metrics, total_sales_metrics = itunes_connect.get_sales_metrics(vendor, requested_date)
    for app_metrics in app_sales_metrics:
      app_metrics['app'] = app_metrics['app'].to_dict()

  else:
    app_sales_metrics, total_sales_metrics = None, None

  return api_response({
    'status': status,

    'appSalesMetrics': app_sales_metrics,
    'totalSalesMetrics': total_sales_metrics,

    'date': APIModel.date_to_api_date(requested_date),
    'vendor': vendor.to_dict(),
  })


@api_user_view('GET', 'POST')
def subscriptions_view(request):
  if request.method == 'GET':
    return _subscriptions_view_GET(request)
  else:
    return _subscriptions_view_POST(request)


def _subscriptions_view_GET(request):
  my_subscriptions = appstore_sales_report_subscriptions.subscriptions_for_user(request.user)
  return api_response({
    'subscriptions': [s.to_dict() for s in my_subscriptions],
  })


def _subscriptions_view_POST(request):
  form = NewSubscriptionForm(request.POST)
  if not form.is_valid():
    return bad_request('Invalid subscription data.', errors=form.errors)

  email = form.cleaned_data.get('email')
  my_email = form.cleaned_data.get('my_email')
  slack_url = form.cleaned_data.get('slack_url')
  slack_channel_name = form.cleaned_data.get('slack_channel_name')

  sub = None
  if email:
    sub = appstore_sales_report_subscriptions.create_email_subscription(request.user, email)
  elif my_email:
    sub = appstore_sales_report_subscriptions.create_my_email_subscription(request.user)
  elif slack_channel_name:
    sub = appstore_sales_report_subscriptions.create_slack_channel_subscription(request.user, slack_channel_name)
  elif slack_url:
    sub = appstore_sales_report_subscriptions.create_slack_subscription(request.user, slack_url)

  if not sub:
    return bad_request('Subscription already exists.')

  new_flags = []
  if not request.user.flags.has_sales_monitor:
    new_flags.append('has_sales_monitor')

  if new_flags:
    request.user.set_flags(new_flags)

  return api_response({
    'subscription': sub.to_dict(),
  })


@api_user_view('POST')
def subscription_delete_view(request, subscription_id=None):
  sub = appstore_sales_report_subscriptions.get_user_subscription_by_encrypted_id(request.user, subscription_id)
  if not sub:
    return not_found()

  appstore_sales_report_subscriptions.disable_subscription(sub)

  return ok_response()


@api_view('POST')
def subscription_unsubscribe_token_view(request):
  sub = itunes_connect.subscription_from_unsubscribe_token(request.POST.get('token', ''))
  if not sub:
    return bad_request('Could not find subscription with that `token`.')

  appstore_sales_report_subscriptions.disable_subscription(sub)

  return ok_response()
