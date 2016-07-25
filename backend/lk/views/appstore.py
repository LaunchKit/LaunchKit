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

from backend.lk.logic import appstore_fetch
from backend.lk.views.base import api_response
from backend.lk.views.base import api_view
from backend.lk.views.base import bad_request
from backend.lk.views.base import not_found



@api_view('GET')
def summary_view(request, country=None, app_id=None):
  app_info = appstore_fetch.app_info_with_id(app_id, country)
  if not app_info:
    return not_found()

  try:
    related_app_infos = appstore_fetch.related_app_infos_with_developer_id(app_info.developer_id, country)
  except:
    logging.exception('Problem fetching related app info')
    related_app_infos = []

  return api_response({
    'app': app_info.to_dict(),
    'related': [ai.to_tiny_dict() for ai in related_app_infos
                if ai.itunes_id != app_info.itunes_id],
  })

