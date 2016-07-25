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

from django.db import connection
from django.db import transaction

from backend.lk.models import AppWebsite
from backend.lk.logic import oauth
from backend.lk.logic import tokens
from backend.lk.logic import websites


DELETE_ACCOUNT_STATEMENTS = (
  'delete from lk_slackaccesstoken where user_id=%s',
  'delete from lk_twitteraccesstoken where user_id=%s',

  "update lk_appstoresalesreportsubscription set enabled='f' where user_id=%s",
  "update lk_appstorereviewsubscription set enabled='f' where user_id=%s",

  "update lk_useremail set email = email || ':deleted@' || extract(epoch from now()) where user_id=%s",
  'delete from lk_userphone where user_id=%s',

  'update lk_screenshotset set delete_time=now() where user_id=%s',

  """
    update lk_user
      set delete_time = now(),
          email = email || ':deleted@' || extract(epoch from now()),
          flags = flags | (1 << 1)
    where id=%s
  """,
)

@transaction.atomic()
def delete_account(user):
  # Need to do this to free up domain.
  for website in AppWebsite.objects.filter(user=user, delete_time__isnull=True):
    websites.delete_website(website)

  # oauth access tokens for website / app access -- INCLUDING CACHE
  oauth.invalidate_tokens_for_user(user)

  # api access tokens -- INCLUDING CACHE
  all_tokens = tokens.get_my_tokens(user)
  for token in all_tokens:
    tokens.expire_token(token)

  # delete all itunes auth stuff & personal info
  delete_itunes_connection_and_imports(user)

  # remove personal information, mark account deleted
  cursor = connection.cursor()
  for statement in DELETE_ACCOUNT_STATEMENTS:
    num_ids = statement.count('%s')
    assert num_ids > 0
    cursor.execute(statement, [user.id] * num_ids)

  user.invalidate_cache()


DELETE_ITUNES_STATEMENTS = (
  # Remove existing reports.
  'delete from lk_appstoresalesreport where vendor_id in (select id from lk_itunesconnectvendor where user_id=%s)',
  'delete from lk_appstoresalesreportfetchedstatus where vendor_id in (select id from lk_itunesconnectvendor where user_id=%s)',

  # Removing existing vendors and access tokens.
  'delete from lk_itunesconnectvendor where user_id = %s',
  'delete from lk_itunesconnectaccesstoken where user_id = %s',
)

@transaction.atomic()
def delete_itunes_connection_and_imports(user):
  cursor = connection.cursor()
  for statement in DELETE_ITUNES_STATEMENTS:
    num_ids = statement.count('%s')
    assert num_ids > 0
    cursor.execute(statement, [user.id] * num_ids)
