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

import redis
from django.conf import settings


if settings.REDIS_URL:
  _redis_client = redis.StrictRedis.from_url(settings.REDIS_URL, socket_timeout=3)
else:
  # This should only happen in testing environments.
  _redis_client = None


def client():
  success = False
  connection = _redis_client.connection_pool.get_connection('get')
  try:
    # Force redis to actually attempt connecting right now.
    connection.connect()
    success = True
  except redis.ConnectionError:
    logging.exception('Could not connect to redis.')
  finally:
    _redis_client.connection_pool.release(connection)

  if success:
    return _redis_client
  else:
    return None
