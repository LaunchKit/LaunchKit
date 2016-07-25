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

from backend.lk.logic import redis_wrap
from backend.lk.models import User


def passes_health_check():
  try:
    users = list(User.objects.all()[:1])
  except Exception as e:
    # Note: This won't usually happen because
    # session middleware will try accessing the DB cursor before we
    # get here, which will cause an error farther up the stack.
    return 'Database unreachable with error: %s' % e

  if not users or not users[0].date_joined:
    return 'Could not find a user, database must be FUBAR'

  redis = redis_wrap.client()
  if not redis:
    return 'Redis unreachable, see log for more detail'

  try:
    redis.echo('Hello, world!')
  except Exception as e:
    return 'Redis unreachable with error: %s' % e

  return None
