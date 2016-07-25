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

import urllib

from backend.lk.models import AppStoreApp
from backend.lk.models import AppStoreReview
from backend.lk.models import TwitterAppConnection
from backend.lk.logic import appstore
from backend.lk.logic import twitter
from backend.lk.logic import twitter_app_connections
from backend.lk.views.base import api_response
from backend.lk.views.base import api_user_view
from backend.lk.views.base import bad_request
from backend.lk.views.base import ok_response
from backend.lk.views.base import unavailable_response


@api_user_view('GET')
def connect_twitter_view(request):
  app_id = request.GET['app_id']
  cb_url = None
  if 'callback_url' in request.GET:
    cb_url = urllib.unquote(request.GET['callback_url'])
  twitter_connect_url = twitter.get_auth_redirect(app_id, cb_url)

  if not twitter_connect_url:
    return unavailable_response()

  return api_response({
    'twitterConnectUrl': twitter_connect_url,
  })


@api_user_view('POST')
def connect_twitter_finish_view(request):
  token = request.POST['token']
  verifier = request.POST['verifier']

  success, twitter_handle = twitter.finish_auth(request.user, token, verifier)
  if not success:
    return bad_request()

  app_id = request.POST['app_id']
  if app_id:
    app = AppStoreApp.find_by_encrypted_id(app_id)
    twitter_app_connections.create_connection(request.user, twitter_handle, app)

  return ok_response()


@api_user_view('POST')
def tweet_review(request):
  twitter_handle = request.POST['twitter_handle']
  review_id = request.POST['review_id']
  review = AppStoreReview.find_by_encrypted_id(review_id)
  tweet_text = request.POST['tweet_text']

  if twitter_handle and review and tweet_text:
    success = twitter.tweet_review(request.user, twitter_handle, review, tweet_text)
    if success:
      return ok_response()

  return bad_request()


@api_user_view('GET')
def get_twitter_app_connections_view(request):
  my_apps = appstore.my_apps(request.user)
  my_apps_by_id = dict((app.id, app) for app in my_apps)

  # FIXME: Remove twitter connections when removing app interests?
  my_connections = [c for c in twitter_app_connections.get_connections_for_user(request.user)
                    if c.app_id in my_apps_by_id]
  my_connected_app_ids = set(c.app_id for c in my_connections)

  for connection in my_connections:
    # update with a decorated app
    connection.app = my_apps_by_id[connection.app_id]
  connections = sorted(my_connections, key=lambda c: c.app.short_name)

  unconnected_apps = sorted([a for a in my_apps if a.id not in my_connected_app_ids],
                            key=lambda a: a.short_name)

  return api_response({
    'connections': [c.to_dict() for c in connections],
    'unconnectedApps': [a.to_dict() for a in unconnected_apps],
    'handles': request.user.twitter_handles,
  })


@api_user_view('POST')
def connect_app_view(request):
  twitter_handle = request.POST['twitter_handle']
  app_id = request.POST['app_id']
  app = AppStoreApp.find_by_encrypted_id(app_id)

  twitter_app_connections.create_connection(request.user, twitter_handle, app)
  return ok_response()


@api_user_view('POST')
def disconnect_app_view(request):
  connection_id = request.POST['connection_id']
  connection = TwitterAppConnection.find_by_encrypted_id(connection_id)

  twitter_app_connections.disconnect(request.user, connection)
  return ok_response()
