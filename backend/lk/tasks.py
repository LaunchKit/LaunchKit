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

# Load modules that contain @celery.task's so we properly register them with the worker.
from backend.lk.logic import appstore_review_ingestion
from backend.lk.logic import appstore_review_subscriptions
from backend.lk.logic import debug
from backend.lk.logic import gae_photos
from backend.lk.logic import itunes_connect
from backend.lk.logic import screenshot_bundler
from backend.lk.logic import sessions
from backend.lk.logic import session_user_labels
from backend.lk.logic import users
