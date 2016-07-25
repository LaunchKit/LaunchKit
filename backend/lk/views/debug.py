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

from backend.lk.logic import debug
from backend.lk.views.base import api_view
from backend.lk.views.base import ok_response
from backend.lk.views.base import unavailable_response


#
# DEBUG
#


@api_view('GET')
def health_check(request):
  health_check_error = debug.passes_health_check()
  if not health_check_error:
    return ok_response()
  return unavailable_response(message=health_check_error)
