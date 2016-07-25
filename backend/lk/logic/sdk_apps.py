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

from django.db.models import Q

from backend.lk.models import SDKApp
from backend.lk.logic import appstore_app_info
from backend.lk.logic import session_user_labels
from backend.lk.logic.session_user_labels import ActiveStatus


#
# MY APPS
#


def decorated_apps_by_id(app_ids, load_config_children=False):
  filters = Q(id__in=app_ids)
  if load_config_children:
    filters |= Q(config_parent_id__in=app_ids)
  apps = list(SDKApp.objects.filter(filters))

  counts_by_app = session_user_labels.label_counts_by_app_ids([a.id for a in apps])
  for app in apps:
    app.decorated_label_counts = counts_by_app[app.id]

    if app.appstore_app_id:
      appstore_app_info.decorate_app(app.appstore_app, app.appstore_app_country)

  if load_config_children:
    parent_apps = []
    apps_by_id = {}
    for app in apps:
      apps_by_id[app.id] = app
      if app.decorated_config_children is None:
        app.decorated_config_children = []

    for app in apps:
      parent = apps_by_id.get(app.config_parent_id)
      if parent:
        parent.decorated_config_children.append(app)
      else:
        parent_apps.append(app)

  else:
    parent_apps = apps

  return sorted(parent_apps, key=lambda a: a.decorated_label_counts.get(ActiveStatus.MonthlyActive, 0), reverse=True)


def decorated_app_by_id(app_id):
  apps = decorated_apps_by_id([app_id], load_config_children=True)
  if apps:
    return apps[0]
  return None


def decorated_app_by_bundle_id(user, bundle_id):
  app = create_or_fetch_sdk_app_with_bundle_id(user, bundle_id)
  return decorated_app_by_id(app.id)


def my_decorated_apps(user, only_config_parents=False, product=None):
  my_apps = SDKApp.objects.filter(user=user)
  if only_config_parents:
    my_apps = my_apps.filter(config_parent_id__isnull=True)
  if product:
    my_apps = my_apps.extra(where=['(products->%s)::int = 1'], params=[product])

  app_ids = my_apps.values_list('id', flat=True)[:100]
  return decorated_apps_by_id(app_ids)


def create_or_decorate_sdk_app_with_appstore_app(user, appstore_app):
  existing_app = SDKApp.objects.filter(user=user, bundle_id=appstore_app.bundle_id).select_for_update().first()
  if existing_app:
    existing_app.appstore_app = appstore_app
    existing_app.appstore_app_country = appstore_app.decorated_country
    existing_app.save()
    return existing_app

  sdk_app = SDKApp(user=user, bundle_id=appstore_app.bundle_id,
      appstore_app=appstore_app, appstore_app_country=appstore_app.decorated_country)
  sdk_app.save()

  return sdk_app


def create_or_fetch_sdk_app_with_bundle_id(user, bundle_id):
  sdk_app = SDKApp.objects.filter(user=user, bundle_id=bundle_id).first()

  if not sdk_app:
    sdk_app = SDKApp(user=user, bundle_id=bundle_id)
    # NOTE: Don't do a get_or_create here because we're setting config.
    sdk_app.save()

  return sdk_app
