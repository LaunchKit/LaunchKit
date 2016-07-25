# encoding: utf-8
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

from django.db import transaction

from backend.lk.logic import appstore_app_info
from backend.lk.logic import appstore_fetch
from backend.lk.logic import appstore_review_ingestion
from backend.lk.logic import appstore_review_notify
from backend.lk.models import AppStoreApp
from backend.lk.models import AppStoreAppInterest
from backend.lk.models import AppStoreAppReviewTracker


@transaction.atomic
def get_app_by_itunes_id(itunes_id, country):
  try:
    long(itunes_id)
  except (ValueError, TypeError):
    return None

  try:
    app = AppStoreApp.objects.get(itunes_id=itunes_id)
  except AppStoreApp.DoesNotExist:
    app = None

  if app and app.app_info_countries and country in app.app_info_countries:
    appstore_app_info.decorate_app(app, country)
    return app

  app_info = appstore_fetch.app_info_with_id(itunes_id, country)
  if not app_info:
    return None

  if not app:
    app = AppStoreApp(itunes_id=app_info.itunes_id, bundle_id=app_info.bundle_id)

  if not app.app_info_countries:
    app.app_info_countries = [country]
  elif country not in app.app_info_countries:
    app.app_info_countries.append(country)
  app.save()

  appstore_app_info.mark_app_needs_info_ingestion(app)
  appstore_app_info.update_app_info_with_fetched_data(app, app_info)
  appstore_app_info.decorate_app(app, country)

  return app


@transaction.atomic
def get_app_by_bundle_id(bundle_id, country):
  try:
    app = AppStoreApp.objects.get(bundle_id=bundle_id)
  except AppStoreApp.DoesNotExist:
    app = None

  if app and app.app_info_countries and country in app.app_info_countries:
    appstore_app_info.decorate_app(app, country)
    return app

  app_info = appstore_fetch.app_info_with_bundle_id(bundle_id, country)
  if not app_info:
    return None

  if not app:
    app = AppStoreApp(itunes_id=app_info.itunes_id, bundle_id=app_info.bundle_id)

  if not app.app_info_countries:
    app.app_info_countries = [country]
  elif country not in app.app_info_countries:
    app.app_info_countries.append(country)
  app.save()

  appstore_app_info.mark_app_needs_info_ingestion(app)
  appstore_app_info.update_app_info_with_fetched_data(app, app_info)
  appstore_app_info.decorate_app(app, country)

  return app



@transaction.atomic
def get_app_and_related_by_itunes_id(itunes_id, country):
  app_info = appstore_fetch.app_info_with_id(itunes_id, country)
  if not app_info:
    return None

  app_infos = appstore_fetch.related_app_infos_with_developer_id(app_info.developer_id, country)
  app_infos_by_itunes_id = dict((a.itunes_id, a) for a in app_infos)

  existing_app_ids = AppStoreApp.objects.filter(
      itunes_id__in=app_infos_by_itunes_id.keys()).values_list('itunes_id', flat=True)
  existing_app_ids = set(long(i) for i in existing_app_ids)

  apps_to_insert = [AppStoreApp(itunes_id=a.itunes_id, bundle_id=a.bundle_id)
                    for a in app_infos if long(a.itunes_id) not in existing_app_ids]
  if apps_to_insert:
    AppStoreApp.objects.bulk_create(apps_to_insert)

  fetched_apps = list(AppStoreApp.objects.filter(
      itunes_id__in=[str(i) for i in app_infos_by_itunes_id]))

  for app in fetched_apps:
    app_info = app_infos_by_itunes_id[long(app.itunes_id)]
    if not app.app_info_countries:
      app.app_info_countries = [country]
    else:
      app.app_info_countries.append(country)
    app.save()

    appstore_app_info.mark_app_needs_info_ingestion(app)
    appstore_app_info.update_app_info_with_fetched_data(app, app_info)
    appstore_app_info.decorate_app(app, country)

  return fetched_apps


def mark_interested_in_apps(user, apps, country):
  for app in apps:
    obj, _ = AppStoreAppInterest.objects.get_or_create(user=user, app=app, country=country)
    if not obj.enabled:
      obj.enabled = True
      obj.save(update_fields=['enabled', 'update_time'])

      mark_app_should_track_reviews(app, country)

      if not user.flags.any_reviews_pending:
        user.set_flags(['any_reviews_pending'])

  appstore_review_notify.maybe_notify_subs_apps_added(user, apps, country)


def mark_not_interested_in_app(user, app, country):
  try:
    interest = AppStoreAppInterest.objects.select_related('app').get(user=user, app=app, country=country, enabled=True)
  except AppStoreAppInterest.DoesNotExist:
    return False

  interest.enabled = False
  interest.save(update_fields=['update_time', 'enabled'])

  maybe_disable_review_tracking_for_app(interest.app)

  return True


def my_apps(user, limit=50):
  my_interests = AppStoreAppInterest.objects.filter(user=user, enabled=True).order_by('id').select_related('app')[:limit]
  apps = []
  for interest in my_interests:
    appstore_app_info.decorate_app(interest.app, interest.country)
    apps.append(interest.app)

  return sorted(apps, key=lambda a: a.name.lower())


def mark_app_should_track_reviews(app, country):
  AppStoreAppReviewTracker.objects.get_or_create(app=app, country=country)
  appstore_review_ingestion.mark_app_needs_ingestion(app, country)


def mark_should_track_reviews_for_my_apps(user):
  interests = AppStoreAppInterest.objects.filter(user=user, enabled=True).select_related('app')
  my_apps = []
  for interest in interests:
    appstore_app_info.decorate_app(interest.app, interest.country)
    mark_app_should_track_reviews(interest.app, interest.country)
    my_apps.append(interest.app)
  return my_apps


def maybe_disable_review_tracking_for_app(app):
  # TODO(Taylor): Maybe do this eventually if we actually care about doing it.
  pass

def maybe_disable_review_tracking_for_my_apps(user):
  # TODO(Taylor): Look at my interested apps, check if anybody cares anymore, etc.
  pass


APPSTORE_COUNTRIES = (
  ('ae', 'United Arab Emirates'),
  ('ag', 'Antigua and Barbuda'),
  ('ai', 'Anguilla'),
  ('al', 'Albania'),
  ('am', 'Armenia'),
  ('ao', 'Angola'),
  ('ar', 'Argentina'),
  ('at', 'Austria'),
  ('au', 'Australia'),
  ('az', 'Azerbaijan'),
  ('bb', 'Barbados'),
  ('be', 'Belgium'),
  ('bf', 'Burkina Faso'),
  ('bg', 'Bulgaria'),
  ('bh', 'Bahrain'),
  ('bj', 'Benin'),
  ('bm', 'Bermuda'),
  ('bn', 'Brunei'),
  ('bo', 'Bolivia'),
  ('br', 'Brazil'),
  ('bs', 'Bahamas'),
  ('bt', 'Bhutan'),
  ('bw', 'Botswana'),
  ('by', 'Belarus'),
  ('bz', 'Belize'),
  ('ca', 'Canada'),
  ('cg', 'Republic Of Congo'),
  ('ch', 'Switzerland'),
  ('cl', 'Chile'),
  ('cn', 'China'),
  ('co', 'Colombia'),
  ('cr', 'Costa Rica'),
  ('cv', 'Cape Verde'),
  ('cy', 'Cyprus'),
  ('cz', 'Czech Republic'),
  ('de', 'Germany'),
  ('dk', 'Denmark'),
  ('dm', 'Dominica'),
  ('do', 'Dominican Republic'),
  ('dz', 'Algeria'),
  ('ec', 'Ecuador'),
  ('ee', 'Estonia'),
  ('eg', 'Egypt'),
  ('es', 'Spain'),
  ('fi', 'Finland'),
  ('fj', 'Fiji'),
  ('fm', 'Federated States Of Micronesia'),
  ('fr', 'France'),
  ('gb', 'United Kingdom'),
  ('gd', 'Grenada'),
  ('gh', 'Ghana'),
  ('gm', 'Gambia'),
  ('gr', 'Greece'),
  ('gt', 'Guatemala'),
  ('gw', 'Guinea-Bissau'),
  ('gy', 'Guyana'),
  ('hk', 'Hong Kong'),
  ('hn', 'Honduras'),
  ('hr', 'Croatia'),
  ('hu', 'Hungary'),
  ('id', 'Indonesia'),
  ('ie', 'Ireland'),
  ('il', 'Israel'),
  ('in', 'India'),
  ('is', 'Iceland'),
  ('it', 'Italy'),
  ('jm', 'Jamaica'),
  ('jo', 'Jordan'),
  ('jp', 'Japan'),
  ('ke', 'Kenya'),
  ('kg', 'Kyrgyzstan'),
  ('kh', 'Cambodia'),
  ('kn', 'St. Kitts and Nevis'),
  ('kr', 'Republic Of Korea'),
  ('kw', 'Kuwait'),
  ('ky', 'Cayman Islands'),
  ('kz', 'Kazakstan'),
  ('la', 'Lao People’s Democratic Republic'),
  ('lb', 'Lebanon'),
  ('lc', 'St. Lucia'),
  ('lk', 'Sri Lanka'),
  ('lr', 'Liberia'),
  ('lt', 'Lithuania'),
  ('lu', 'Luxembourg'),
  ('lv', 'Latvia'),
  ('md', 'Republic Of Moldova'),
  ('mg', 'Madagascar'),
  ('mk', 'Macedonia'),
  ('ml', 'Mali'),
  ('mn', 'Mongolia'),
  ('mo', 'Macau'),
  ('mr', 'Mauritania'),
  ('ms', 'Montserrat'),
  ('mt', 'Malta'),
  ('mu', 'Mauritius'),
  ('mw', 'Malawi'),
  ('mx', 'Mexico'),
  ('my', 'Malaysia'),
  ('mz', 'Mozambique'),
  ('na', 'Namibia'),
  ('ne', 'Niger'),
  ('ng', 'Nigeria'),
  ('ni', 'Nicaragua'),
  ('nl', 'Netherlands'),
  ('no', 'Norway'),
  ('np', 'Nepal'),
  ('nz', 'New Zealand'),
  ('om', 'Oman'),
  ('pa', 'Panama'),
  ('pe', 'Peru'),
  ('pg', 'Papua New Guinea'),
  ('ph', 'Philippines'),
  ('pk', 'Pakistan'),
  ('pl', 'Poland'),
  ('pt', 'Portugal'),
  ('pw', 'Palau'),
  ('py', 'Paraguay'),
  ('qa', 'Qatar'),
  ('ro', 'Romania'),
  ('ru', 'Russia'),
  ('sa', 'Saudi Arabia'),
  ('sb', 'Solomon Islands'),
  ('sc', 'Seychelles'),
  ('se', 'Sweden'),
  ('sg', 'Singapore'),
  ('si', 'Slovenia'),
  ('sk', 'Slovakia'),
  ('sl', 'Sierra Leone'),
  ('sn', 'Senegal'),
  ('sr', 'Suriname'),
  ('st', 'Sao Tome and Principe'),
  ('sv', 'El Salvador'),
  ('sz', 'Swaziland'),
  ('tc', 'Turks and Caicos'),
  ('td', 'Chad'),
  ('th', 'Thailand'),
  ('tj', 'Tajikistan'),
  ('tm', 'Turkmenistan'),
  ('tn', 'Tunisia'),
  ('tr', 'Turkey'),
  ('tt', 'Trinidad and Tobago'),
  ('tw', 'Taiwan'),
  ('tz', 'Tanzania'),
  ('ua', 'Ukraine'),
  ('ug', 'Uganda'),
  ('us', 'United States'),
  ('uy', 'Uruguay'),
  ('uz', 'Uzbekistan'),
  ('vc', 'St. Vincent and The Grenadines'),
  ('ve', 'Venezuela'),
  ('vg', 'British Virgin Islands'),
  ('vn', 'Vietnam'),
  ('ye', 'Yemen'),
  ('za', 'South Africa'),
  ('zw', 'Zimbabwe'),
)
APPSTORE_COUNTRIES_BY_CODE = dict(APPSTORE_COUNTRIES)

