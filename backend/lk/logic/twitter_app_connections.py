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

from backend.lk.logic import appstore_review_subscriptions
from backend.lk.models import TwitterAppConnection


def get_connections_for_user(user):
  return list(
    TwitterAppConnection.objects
    .filter(user=user, enabled=True)
    .select_related('app', 'subscription'))


def create_connection(user, twitter_handle, app):
  if twitter_handle not in user.twitter_handles:
    return None

  connections = TwitterAppConnection.objects.filter(user=user, app=app, handle=twitter_handle)
  if connections:
    connection = connections[0]
  else:
    connection = TwitterAppConnection(handle=twitter_handle, user=user, app=app)

  connection.enabled = True
  connection.save()

  return connection


def disconnect(user, connection):
  if connection.user == user:
    connection.enabled = False
    connection.save()
