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

from django import forms
from django.core import validators

from backend.lk.logic import appstore
from backend.lk.logic import appstore_app_info
from backend.lk.logic import appstore_review_notify
from backend.lk.logic import appstore_review_subscriptions
from backend.lk.models import AppStoreApp
from backend.lk.models import AppStoreReview
from backend.lk.models import TwitterAppConnection
from backend.lk.views.base import api_response
from backend.lk.views.base import api_view
from backend.lk.views.base import api_user_view
from backend.lk.views.base import bad_request
from backend.lk.views.base import not_found
from backend.lk.views.base import ok_response
from backend.util import lkforms


class NewSubscriptionForm(forms.Form):
  email = lkforms.LKEmailField(required=False)
  my_email = lkforms.LKBooleanField(required=False)

  twitter_app_connection_id = lkforms.LKEncryptedIdReferenceField(TwitterAppConnection, required=False)
  app_id = lkforms.LKEncryptedIdReferenceField(AppStoreApp, required=False)

  slack_channel_name = forms.CharField(required=False, max_length=64)

  slack_url = forms.URLField(required=False)

  def clean_slack_url(self):
    slack_url = self.cleaned_data.get('slack_url')
    if slack_url:
      if urlparse.urlparse(slack_url).netloc != 'hooks.slack.com' or '/services/' not in slack_url:
        raise forms.ValidationError('Slack URL should be a hooks.slack.com URL and start with /services/.')
    return slack_url

  def clean(self):
    email = self.cleaned_data.get('email')
    slack_url = self.cleaned_data.get('slack_url')
    my_email = self.cleaned_data.get('my_email', False)
    slack_channel_name = self.cleaned_data.get('slack_channel_name', False)
    twitter_app_connection = self.cleaned_data.get('twitter_app_connection_id')
    app = self.cleaned_data.get('app_id')

    # the form is considered legit if it contains just one of the parameters for creating a review subsciption
    legit = len(filter(lambda x: x, [slack_url, email, my_email, slack_channel_name, twitter_app_connection, app])) == 1

    if not legit:
      raise forms.ValidationError(
          'Please provide `email` or `slack_url` or `my_email` or `slack_channel` or `twitter_app_connection_id` or `app_id`, but just one.')

    return self.cleaned_data


class ReviewsFilter(forms.Form):
  start_review_id = lkforms.LKEncryptedIdReferenceField(AppStoreReview, required=False)
  app_id = lkforms.LKEncryptedIdReferenceField(AppStoreApp, required=False)
  country = forms.ChoiceField(choices=appstore.APPSTORE_COUNTRIES, required=False)
  rating = forms.IntegerField(required=False, min_value=1, max_value=5)
  limit = forms.IntegerField(required=False, min_value=1, max_value=200)


@api_user_view('GET')
def reviews_view(request):
  form = ReviewsFilter(request.GET)
  if not form.is_valid():
    return bad_request('Invalid filters provided.', errors=form.errors)

  filters = form.cleaned_data
  start_review = filters.get('start_review_id')
  my_reviews = appstore_review_subscriptions.subscribed_reviews_for_user(request.user,
      app=filters.get('app_id'),
      country=filters.get('country'),
      rating=filters.get('rating'),
      start_review=start_review,
      limit=filters.get('limit'))

  # TODO(Taylor): Remove app id:app 1:1 relationship; move to app id + country
  apps = set()
  for review in my_reviews:
    if review.app not in apps:
      apps.add(review.app)

  return api_response({
    'reviews': [r.to_dict() for r in my_reviews],
    'apps': dict((a.encrypted_id, a.to_dict()) for a in apps),
  })


@api_view('GET')
def review_view(request, review_id=None):
  review = AppStoreReview.find_by_encrypted_id(review_id)
  if not review:
    return not_found()

  app = review.app
  appstore_app_info.decorate_app(app, review.country)

  return api_response({
    'review': review.to_dict(),
    'apps': {app.encrypted_id: app.to_dict()}
  })


@api_user_view('GET', 'POST')
def subscriptions_view(request):
  if request.method == 'GET':
    return _subscriptions_view_GET(request)
  else:
    return _subscriptions_view_POST(request)


def _subscriptions_view_GET(request):
  my_subscriptions = appstore_review_subscriptions.subscriptions_for_user(request.user)
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
  twitter_app_connection = form.cleaned_data.get('twitter_app_connection_id')

  app = form.cleaned_data.get('app_id')
  if app and not twitter_app_connection:
    try:
      twitter_app_connection = TwitterAppConnection.objects.get(user=request.user, app=app, enabled=True)
    except TwitterAppConnection.DoesNotExist:
      return bad_request('Invalid `app_id`, not already connected to twitter.')

  sub = None
  if email:
    sub = appstore_review_subscriptions.create_email_subscription(request.user, email)
  elif my_email:
    sub = appstore_review_subscriptions.create_my_email_subscription(request.user)
  elif slack_channel_name:
    sub = appstore_review_subscriptions.create_slack_channel_subscription(request.user, slack_channel_name)
  elif slack_url:
    sub = appstore_review_subscriptions.create_slack_subscription(request.user, slack_url)
  elif twitter_app_connection:
    sub = appstore_review_subscriptions.create_twitter_subscription_from_connection(twitter_app_connection)

  if not sub:
    return bad_request('Subscription already exists.')


  new_flags = []
  if not request.user.flags.has_review_monitor:
    new_flags.append('has_review_monitor')
  if sub.twitter_connection_id and not request.user.flags.has_review_monitor_tweets:
    new_flags.append('has_review_monitor_tweets')

  if new_flags:
    request.user.set_flags(new_flags)

  return api_response({
    'subscription': sub.to_dict(),
  })


@api_user_view('GET', 'POST')
def subscription_view(request, subscription_id=None):
  sub = appstore_review_subscriptions.get_user_subscription_by_encrypted_id(request.user, subscription_id)
  if not sub:
    return not_found()

  if request.method == 'GET':
    return api_response({
      'subscription': sub.to_dict(),
    })

  if request.POST.get('filter_good'):
    do_filter = request.POST['filter_good'] == '1'
    appstore_review_subscriptions.mark_subscription_filtered_good(sub, do_filter)

  return api_response({
    'subscription': sub.to_dict(),
  })


@api_user_view('POST')
def subscription_delete_view(request, subscription_id=None):
  sub = appstore_review_subscriptions.get_user_subscription_by_encrypted_id(request.user, subscription_id)
  if not sub:
    return not_found()

  appstore_review_subscriptions.disable_subscription(sub)

  return ok_response()


@api_view('POST')
def subscription_unsubscribe_token_view(request):
  sub = appstore_review_notify.subscription_from_unsubscribe_token(request.POST.get('token', ''))
  if not sub:
    return bad_request('Could not find subscription with that `token`.')

  appstore_review_subscriptions.disable_subscription(sub)

  return ok_response()
