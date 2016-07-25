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

import StringIO
import collections
import copy
import csv
import json
import logging
import math
import pytz
import time
import zlib
from datetime import datetime
from datetime import timedelta

import requests
from celery.exceptions import TimeoutError
from django.conf import settings
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.db import transaction
from django.db.models import Q
from django.core.cache import cache

from backend.lk.logic import appstore
from backend.lk.logic import appstore_app_info
from backend.lk.logic import crypto_hack
from backend.lk.logic import emails
from backend.lk.logic import slack
from backend.lk.models import AppStoreApp
from backend.lk.models import AppStoreSalesReport
from backend.lk.models import AppStoreSalesReportFetchedStatus
from backend.lk.models import AppStoreSalesReportNotification
from backend.lk.models import AppStoreSalesReportSubscription
from backend.lk.models import ItunesConnectAccessToken
from backend.lk.models import ItunesConnectVendor
from backend.lk.models import User
from backend.util import urlutil
from backend import celery_app


REPORT_STATUS_AVAILABLE = 'available'
REPORT_STATUS_FAILED = 'failed'
REPORT_STATUS_PENDING = 'pending'
REPORT_STATUS_EMPTY = 'empty'
REPORT_STATUS_UNAVAILABLE = 'unavailable'


FALLBACK_USD_CONVERSION_DICT = {
  'aed': 3.67295,
  'afn': 60.01981,
  'all': 124.569504,
  'amd': 473.420013,
  'ang': 1.789794,
  'aoa': 119.720001,
  'ars': 9.066796,
  'aud': 1.286505,
  'awg': 1.79,
  'azn': 1.048897,
  'bam': 1.7242,
  'bbd': 2,
  'bdt': 77.721451,
  'bgn': 1.723898,
  'bhd': 0.37697,
  'bif': 1577.5,
  'bmd': 1,
  'bnd': 1.334702,
  'bob': 6.890117,
  'brl': 3.09765,
  'bsd': 1,
  'btc': 0.004093,
  'btn': 63.549999,
  'bwp': 9.89835,
  'byr': 15325,
  'bzd': 2.015015,
  'cad': 1.226799,
  'cdf': 928.000047,
  'chf': 0.917025,
  'clf': 0.024602,
  'clp': 632.655029,
  'cny': 6.207595,
  'cop': 2551.830078,
  'crc': 534.380005,
  'cuc': 1.00001,
  'cup': 0.999692,
  'cve': 96.849503,
  'czk': 24.023497,
  'djf': 176.895004,
  'dkk': 6.57475,
  'dop': 44.92973,
  'dzd': 98.389999,
  'eek': 13.766993,
  'egp': 7.625097,
  'ern': 15.27989,
  'etb': 20.640499,
  'eur': 0.881026,
  'fjd': 2.07465,
  'fkp': 0.638298,
  'gbp': 0.629782,
  'gel': 2.244996,
  'ggp': 0.63006,
  'ghs': 4.401579,
  'gip': 0.629899,
  'gmd': 42.549999,
  'gnf': 7287.450195,
  'gtq': 7.637502,
  'gyd': 207.210007,
  'hkd': 7.751503,
  'hnl': 21.935196,
  'hrk': 6.675851,
  'htg': 49.578499,
  'huf': 276.019989,
  'idr': 13325.5,
  'ils': 3.826302,
  'imp': 0.63007,
  'inr': 63.463451,
  'iqd': 1192.5,
  'irr': 29126.000294,
  'isk': 130.990005,
  'jep': 0.63004,
  'jmd': 116.207001,
  'jod': 0.70835,
  'jpy': 122.690498,
  'kes': 98.496498,
  'kgs': 60.446201,
  'khr': 4104.950195,
  'kmf': 433.700165,
  'kpw': 899.999924,
  'krw': 1103.545044,
  'kwd': 0.301625,
  'kyd': 0.82013,
  'kzt': 186.059998,
  'lak': 8109.950195,
  'lbp': 1507.496617,
  'lkr': 134.100006,
  'lrd': 84.660004,
  'lsl': 12.16425,
  'ltl': 3.04385,
  'lvl': 0.61955,
  'lyd': 1.36495,
  'mad': 9.62315,
  'mdl': 19.129999,
  'mga': 3166.502819,
  'mkd': 54.279999,
  'mmk': 1109.150024,
  'mnt': 1919.492445,
  'mop': 7.984097,
  'mro': 322.999612,
  'mur': 34.970001,
  'mvr': 15.379743,
  'mwk': 439.994995,
  'mxn': 15.339103,
  'myr': 3.738501,
  'mzn': 38.625014,
  'nad': 12.16425,
  'ngn': 198.949997,
  'nio': 27.209701,
  'nok': 7.731901,
  'npr': 101.679688,
  'nzd': 1.448541,
  'omr': 0.38505,
  'pab': 1,
  'pen': 3.166902,
  'pgk': 2.72965,
  'php': 44.995499,
  'pkr': 101.764999,
  'pln': 3.68245,
  'pyg': 5153.491965,
  'qar': 3.640399,
  'ron': 3.95765,
  'rsd': 106.334999,
  'rub': 54.041499,
  'rwf': 721.049988,
  'sar': 3.75005,
  'sbd': 7.862121,
  'scr': 13.00095,
  'sdg': 5.974956,
  'sek': 8.118098,
  'sgd': 1.333985,
  'shp': 0.6299,
  'sll': 4137.999811,
  'sos': 700.950012,
  'srd': 3.30148,
  'std': 21607.5,
  'svc': 8.742198,
  'syp': 188.822006,
  'szl': 12.16425,
  'thb': 33.640999,
  'tjs': 6.260202,
  'tmt': 3.5,
  'tnd': 1.92795,
  'top': 2.03881,
  'try': 2.692402,
  'ttd': 6.34755,
  'twd': 30.72899,
  'tzs': 2273.300049,
  'uah': 21.700001,
  'ugx': 3283.00022,
  'usd': 1,
  'uyu': 26.724987,
  'uzs': 2546.219971,
  'vef': 6.349987,
  'vnd': 21805,
  'vuv': 108.730003,
  'wst': 2.528663,
  'xaf': 578.266846,
  'xag': 0.062096,
  'xau': 0.000833,
  'xcd': 2.694813,
  'xdr': 0.706897,
  'xof': 578.266846,
  'xpf': 105.198303,
  'yer': 215.050003,
  'zar': 12.15685,
  'zmk': 5156.101353,
  'zmw': 7.410187,
  'zwl': 322.355011
}


APILAYER_KEY = '6e1da7e26722b6ddced025064baf3392'
CONVERSION_DICT_KEY_FMT = 'apilayer-currency-conversion:%s'


def conversion_dict_for_currency(base_currency, force=False):
  base_currency = base_currency.lower()

  key = CONVERSION_DICT_KEY_FMT % base_currency
  conversion_dict = cache.get(key)
  if conversion_dict and not force:
    return conversion_dict

  # non-SSL USD-only is all we can do now.
  fixer_url = urlutil.appendparams('http://www.apilayer.net/api/live?format=1&source=USD',
      access_key=APILAYER_KEY)
  try:
    r = requests.get(fixer_url, timeout=5.0)
  except requests.exceptions.RequestException:
    logging.exception('Itunes Connect Error - could not fetch currency conversion dict (%s)', base_currency)
    r = None

  try:
    response_dict = r and r.json()
  except:
    response_dict = None

  if response_dict and 'quotes' in response_dict and len(response_dict['quotes']) > 100:
    # USD: '0.25' -> usd: 0.25
    conversion_dict = {}
    for k, v in response_dict['quotes'].items():
      conversion_dict[k.lower().replace('usd', '')] = float(v)

  else:
    conversion_dict = copy.copy(FALLBACK_USD_CONVERSION_DICT)

  if base_currency != 'usd':
    usd_to_base = conversion_dict[base_currency]
    for k, v in conversion_dict.items():
      conversion_dict[k] = v / usd_to_base
    del conversion_dict[base_currency]
    conversion_dict['usd'] = 1 / usd_to_base

  cache.set(key, conversion_dict)
  return conversion_dict


def get_freshest_sales_report_date():
  now = pytz.utc.localize(datetime.now())
  now_pacific = now.astimezone(pytz.timezone('US/Pacific'))
  freshest_date = now_pacific.date() - timedelta(1)

  # reports for the previous day only come out by 6 am in the territory of the report, and since US/Pacific
  # is the earliest timezone for all territories Apple reports against, all reports will be avalaible by then
  # NOTE: we run daily ingestion at 6:30 am
  if not now_pacific.hour >= 6:
    freshest_date -= timedelta(1)
  return freshest_date


def date_to_itunes_str_format(d):
  return d.isoformat().replace('-', '')


def formatted_delta(requested, previous):
  if previous == 0:
    return None
  return '%.1f' % (((float(requested) / float(previous)) - 1) * 100)


# right now this is just used to extract nested arrays in an object with the target key
# would have to be generalized for other uses... e.g., extracting non-array values
def deep_search_json(json_obj, target):
  if type(json_obj) is dict:
    keys = [key for key in json_obj]
    if target in keys:
      return json_obj[target]
    for key in keys:
      return reduce(lambda x, a: a + x, [deep_search_json(json_obj[key], target) for key in keys])
  elif type(json_obj) is list:
    return reduce(lambda x, a: a + x, [deep_search_json(o, target) for o in json_obj])
  else:
    return []


def _itunes_creds_for_user_id(user_id):
  token_list = list(ItunesConnectAccessToken.objects.filter(user_id=user_id, invalidated_time__isnull=True)
                    .order_by('-id')[:1])

  if not token_list:
    return None, None

  token = token_list[0]
  return token.apple_id, token.token


def itunes_credentials_email_for_user_id(user_id):
  credentials = list(ItunesConnectAccessToken.objects.filter(user_id=user_id, invalidated_time__isnull=True))
  if credentials:
    return credentials[0].apple_id
  return None


def get_chosen_vendor_for_user(user):
  vendors = list(ItunesConnectVendor.objects.filter(user=user, is_chosen=True).order_by('-id')[:1])
  if not vendors:
    return None
  return vendors[0]


def associate_user_with_itunes_connect(user, apple_id, password):
  # first, check if the user provided valid login credentials for itunes connect
  # if so, we should be able to fetch their itunes connect vendor(s)
  try:
    async_result = _fetch_vendors.delay(apple_id, password)
  except:
    logging.exception('Task queue unavailable')

  try:
    async_result.wait(timeout=16.0)
  except TimeoutError:
    logging.warn('Timed out waiting to fetch vendors from itunes connect')
    return None
  except:
    logging.exception('Task queue error waiting to fetch vendors from itunes connect')
    return None

  vendors_response = async_result.result
  if not vendors_response.vendors:
    return vendors_response

  # if it has gotten this far, the user supplied valid itunes connect credentials
  # so, save their encrypted credentials and vendor(s) with them connected
  try:
    async_result = _associate_user_with_itunes_connect.delay(user.id, apple_id, password, vendors_response.vendors)
  except:
    logging.exception('Task queue unavailable')

  try:
    async_result.wait(timeout=7.0)
  except TimeoutError:
    logging.warn('Timed out waiting to encrypt itunes connect credentials')
    return None
  except:
    logging.exception('Task queue error waiting to encrypt itunes connect credentials')
    return None

  return vendors_response


@celery_app.task(queue='itunesux')
def _associate_user_with_itunes_connect(user_id, apple_id, password, raw_vendors):
  user = User.objects.get(pk=user_id)
  # TODO: Encyrpt this password!
  encrypted_token = password
  token_obj = ItunesConnectAccessToken(user_id=user_id, apple_id=apple_id, token=encrypted_token)
  token_obj.save()

  vendors = []
  for name, itc_id in raw_vendors:
    try:
      vendor = ItunesConnectVendor.objects.get(user_id=user_id, name=name, itc_id=itc_id)
    except ItunesConnectVendor.DoesNotExist:
      vendor = ItunesConnectVendor(user_id=user_id, name=name, itc_id=itc_id, token=token_obj)
      vendor.save()
    vendors.append(vendor)

  if len(vendors) == 1:
    choose_vendor(user, vendors[0])

  return True



VendorsResponse = collections.namedtuple('VendorsResponse', ['auth_error', 'vendors_error', 'connection_error', 'vendors'])
def vendors_response(auth_error=None, vendors_error=None, connection_error=None, vendors=None):
  return VendorsResponse(auth_error, vendors_error, connection_error, vendors)


@celery_app.task(queue='itunesux')
def _fetch_vendors(apple_id, password):
  s = requests.Session()

  auth_creds = {
    'accountName': apple_id,
    'password': password,
    'rememberMe': True
  }

  # don't allow redirects on the login attempt since the easiest way to tell if it worked is if it's a redirect
  try:
    # Magic widgetKey located here:
    #   https://itunesconnect.apple.com/itc/static-resources/controllers/login_cntrl.js
    # via:
    #   https://github.com/fastlane/spaceship/commit/548bee0fad0d24f5bd426bf7fa6254882596229a
    r = s.post('https://idmsa.apple.com/appleauth/auth/signin?widgetKey=22d448248055bab0dc197c6271d738c3',
               headers={'Content-Type': 'application/json'},
               data=json.dumps(auth_creds),
               allow_redirects=False,
               timeout=5.0)
  except requests.exceptions.RequestException as e:
    logging.warn('Itunes Connect - Authentication problem: %s', e)
    return vendors_response(connection_error='iTunes Connect authentication connection error')

  set_session_cookies = r.headers.get('set-cookie')
  if 'myacinfo=' not in set_session_cookies:
    return vendors_response(auth_error='iTunes Connect authentication failed')

  report_response = None
  report_json = None

  try:
    # This sets additional cookies we need for the next request.
    r = s.get('https://itunesconnect.apple.com/WebObjects/iTunesConnect.woa')
  except requests.exceptions.RequestException as e:
    logging.exception('Itunes Connect Error - Failed to fetch vendors')
    return vendors_response(connection_error='iTunes Connect login error')

  set_cookie = r.headers.get('set-cookie') or ''
  if 'wosid=' not in set_cookie:
    logging.info('Itunes Connect - WOSID problem')
    return vendors_response(auth_error='iTunes Connect authentication error "WOSID"')

  # NOTE: Other cookies being present might actually cause the /api/reports
  # request below to return EMPTY! So filter out to just the ones we actually want.
  ONLY_COOKIES_WE_NEED = ('myacinfo', 'itctx')
  vendors_cookies = {cookie.name: cookie.value for cookie in s.cookies if cookie.name in ONLY_COOKIES_WE_NEED}
  if len(vendors_cookies) != len(ONLY_COOKIES_WE_NEED):
    logging.info('Itunes Connect - auth cookies we need not present')
    return vendors_response(auth_error='iTunes Connect authentication error: missing cookies')

  try:
    # This actually fetches the vendors list.
    headers = {'Cookie': ';'.join(['%s=%s' % (k,v) for k,v in vendors_cookies.items()])}
    report_response = requests.get('https://reportingitc2.apple.com/api/reports', timeout=5.0, headers=headers)
  except requests.exceptions.RequestException as e:
    logging.exception('Itunes Connect Error - Failed to fetch vendors')
    return vendors_response(connection_error='iTunes Connect login error')

  try:
    report_json = report_response.json() or {}
  except ValueError as e:
    if report_response.text and 'This request requires HTTP authentication' in report_response.text:
      # commonly happens after we gain access (post-SL9009) but before fully accessible
      logging.info('Itunes Connect - Non-JSON response (401 authentication reqd) for %s', apple_id)
    else:
      logging.info('Itunes Connect - Non-JSON response for %s: %s - %s', apple_id, report_response, report_response.text)
    return vendors_response(vendors_error='iTunes Connect reporting format error')

  vendors_json_objs = deep_search_json(report_json, 'vendors')
  if not vendors_json_objs:
    if report_json.get('error-code') == 'SL4000':
      # {u'error-code': u'SL4000', u'message': u'You have access to multiple content provider Ids.[144196, 1971050]'}
      logging.info('Itunes Connect - multiple content provider IDs issue for apple_id: %s', apple_id)
      return vendors_response(vendors_error='iTunes Connect reporting access error "SL4000"')

    elif report_json.get('error-code') == 'SL9009':
      # {u'error-code': u'SL9009', u'message': u'You do not have access to the application PIANO.'}
      logging.info('Itunes Connect - no access (yet?) for account %s', apple_id)
      return vendors_response(vendors_error='iTunes Connect reporting access error "SL9009"')

    elif report_json.get('error-code') == 'SL5000':
      logging.info('Itunes Connect - SL5000 for account %s', apple_id)
      return vendors_response(vendors_error='iTunes Connect access error — does user have "Reports" role?')

    else:
      logging.error('Itunes Connect Error - No vendors in report JSON! %s', report_json)
      return vendors_response(vendors_error='unknown iTunes Connect reporting error')

  vendors = []
  for vendor in vendors_json_objs:
    itc_id = vendor.get('id')
    name = vendor.get('name', '')
    suffix = ' - %s' % itc_id
    if name.endswith(suffix):
      name = name[:len(name)-len(suffix)]
    else:
      # probably non-breaking...
      logging.warn('Itunes Connect Warning - Apple may have changed the format of vendor names: %s', report_json)

    vendors.append((name, itc_id))

  return vendors_response(vendors=vendors)


def _create_reports_from_tsv(tsv_file, vendor_id):
  # drop column titles in first line of tsv
  lines = list(csv.reader(tsv_file, delimiter='\t'))[1:]

  countries_units_by_itunes_id = collections.defaultdict(lambda: [])

  report_dicts = []
  for l in lines:
    d = {}
    itunes_id = l[14]
    country = l[12].lower()
    d['country_code'] = country
    d['itunes_id'] = itunes_id

    d['vendor_id'] = vendor_id

    try:
      d['begin_date'] = datetime.strptime(l[9], '%m/%d/%Y').date()
      d['end_date'] = datetime.strptime(l[10], '%m/%d/%Y').date()
    except ValueError:
      logging.info('Skipping invalid date from tsv row: %r', l)
      continue

    d['product_type_identifier'] = l[6]
    units = l[7]
    d['units'] = units

    d['customer_currency'] = l[11].lower()
    d['proceeds_currency'] = l[13].lower()
    d['developer_proceeds'] = l[8]

    d['provider'] = l[0]
    d['provider_country'] = l[1].lower()
    d['sku'] = l[2]
    d['title'] = l[4]
    d['version'] = l[5]
    d['customer_price'] = l[15]
    d['promo_code'] = l[16]
    d['parent_identifier'] = l[17]
    d['subscription'] = l[18]
    d['period'] = l[19]
    d['category'] = l[20]
    d['cmb'] = l[21]

    countries_units_by_itunes_id[itunes_id].append((units, country))
    report_dicts.append(d)

  decorated_apps_by_itunes_id = {}
  for itunes_id, units_countries in countries_units_by_itunes_id.items():
    # this will sort by the first item in each tuple, being units, so will return the country with the highest sales
    biggest_unit_country = sorted(countries_units_by_itunes_id[itunes_id], reverse=True)[0]
    _, country = biggest_unit_country
    try:
      decorated_apps_by_itunes_id[itunes_id] = appstore.get_app_by_itunes_id(itunes_id, country)
    except:
      logging.exception('Could not find app with id: %s country: %s in sales report for vendor %s',
          itunes_id, country, vendor_id)

  reports = []
  missing_apps = set()
  for report in report_dicts:
    app = decorated_apps_by_itunes_id.get(report['itunes_id'])
    if not app:
      # This might not be an app, eg. an app bundle
      missing_apps.add(report['itunes_id'])
      continue

    report['app'] = app
    del report['itunes_id']
    reports.append(AppStoreSalesReport(**report))

  if missing_apps:
    logging.info('App(s) missing for report. itunes_ids: %s vendor: %s', list(missing_apps), vendor_id)

  return reports


@celery_app.task(queue='itunesfetch', max_retries=10)
def _fetch_from_itunes(vendor_id, fetch_date, notify=False):
  def retry(base_wait=1.0):
    retries = _fetch_from_itunes.request.retries
    countdown_secs = base_wait * math.pow(2, retries)
    raise _fetch_from_itunes.retry(countdown=countdown_secs)

  vendor = ItunesConnectVendor.objects.get(pk=vendor_id)

  def maybe_notify():
    if notify:
      send_latest_report_for_user_subs.delay(vendor.user_id, fetch_date)

  fetched = AppStoreSalesReportFetchedStatus.objects.filter(vendor=vendor, report_date=fetch_date)[:1]
  if fetched:
    logging.info('Itunes Connect - aborting attempt to load report that was already fetched')
    maybe_notify()
    return

  apple_id, password = _itunes_creds_for_user_id(vendor.user_id)
  if not (apple_id and password):
    logging.error('Itunes Connect Error - Problem fetching user credentials for autoingestion')
    return

  data = {
    'USERNAME': apple_id,
    'PASSWORD': password,
    'VNDNUMBER': vendor.itc_id,
    'TYPEOFREPORT': 'Sales',
    'DATETYPE': 'Daily',
    'REPORTTYPE': 'Summary',
    'REPORTDATE': date_to_itunes_str_format(fetch_date),
  }

  try:
    r = requests.post('https://reportingitc.apple.com/autoingestion.tft', data=data)
  except requests.exceptions.RequestException:
    logging.exception('Itunes Connect Error - Apple may have changed the autoingestion endpoint')
    # Presumably a temporary outage.
    retry()


  error_message = r.headers.get('errormsg')
  if error_message:
    # This is an attempt to fix invalid unicode messages coming back from Apple,
    # which can apparently happen sometimes.
    try:
      error_message = error_message.encode('utf8', 'replace')
    except UnicodeDecodeError:
      error_message = '(unknown unicode error)'

    if 'past 365 days' in error_message:
      # "Daily reports are only available for past 365 days. Please enter a new date."
      # This means the report is probably not ready yet. Retry in awhile.
      logging.info('Itunes Connect - No report yet for vendor: %s date: %s! Retrying in awhile', vendor.itc_id, fetch_date)
      retry(base_wait=(60.0 * 10))
      return # for clarity

    if 'no report available' in error_message and 'selected period' in error_message:
      # "There is no report available to download, for the selected period"
      logging.info('Itunes Connect - No report for vendor: %s date: %s', vendor.itc_id, fetch_date)
      s = AppStoreSalesReportFetchedStatus(vendor=vendor, report_date=fetch_date, empty=True)
      s.save()
      return

    if (('password was entered incorrectly' in error_message) or
          ('password has expired' in error_message) or
          ('valid username and password' in error_message)):
      permanent_failure_reason = 'bad password for vendor'
    elif 'enter a valid vendor number' in error_message:
      # "Please enter a valid vendor number."
      permanent_failure_reason = 'invalid vendor number'
    elif 'two-factor auth' in error_message:
      permanent_failure_reason = 'two-factor auth problem'
    elif 'access to more than one account' in error_message:
      permanent_failure_reason = 'multi-account access problem'
    elif 'access to reports' in error_message:
      permanent_failure_reason = 'no reports access'
    else:
      permanent_failure_reason = None

    if permanent_failure_reason:
      logging.info('Itunes Connect - %s: %s', permanent_failure_reason, vendor.itc_id)
      s = AppStoreSalesReportFetchedStatus(vendor=vendor, report_date=fetch_date, failed=True)
      s.save()
      return

    else:
      logging.error('Itunes Connect Error - Problem getting sales report: %s (vendor: %s - date: %s)',
          error_message, vendor.itc_id, date_to_itunes_str_format(fetch_date))
      retry()
      return # for clarity

  try:
    decompressed = zlib.decompress(r.content, 16 + zlib.MAX_WBITS)
  except zlib.error as e:
    logging.error('Itunes Connect Error - Decompressing failed (vendor: %s - exception: %s)', vendor_id, e)
    # TODO(Taylor, Keith): If this error ever occurs, determine if it is recoverable.
    retry()

  tsv = StringIO.StringIO(decompressed)

  with transaction.atomic():
    reports = _create_reports_from_tsv(tsv, vendor.id)
    if reports:
      AppStoreSalesReport.objects.bulk_create(reports)
    else:
      logging.info('Itunes Connect - No usable report rows for vendor: %s date: %s', vendor.id, fetch_date)
    s = AppStoreSalesReportFetchedStatus(vendor=vendor, report_date=fetch_date)
    s.save()

  maybe_notify()


def report_status_for_vendor_date(vendor, requested_date):
  try:
    status_obj = AppStoreSalesReportFetchedStatus.objects.get(vendor_id=vendor.id, report_date=requested_date)
  except AppStoreSalesReportFetchedStatus.DoesNotExist:
    if datetime.now().date() - requested_date > timedelta(days=14):
      # If there's no fetched status for this thing and it's more than
      # 14 days ago, it's not happening now.
      return REPORT_STATUS_UNAVAILABLE
    else:
      return REPORT_STATUS_PENDING

  if status_obj.empty:
    return REPORT_STATUS_EMPTY
  if status_obj.failed:
    return REPORT_STATUS_FAILED

  return REPORT_STATUS_AVAILABLE


def choose_vendor(user, vendor):
  ItunesConnectVendor.objects.filter(user_id=user.id).update(is_chosen=False)
  ItunesConnectVendor.objects.filter(user_id=user.id, id=vendor.id).update(is_chosen=True)
  vendor.is_chosen = True

  import_initial_sales_reports_for_user_vendor(user, vendor)


def import_initial_sales_reports_for_user_vendor(user, vendor, delay=True):
  start_date = get_freshest_sales_report_date()

  for x in range(14):
    _fetch_from_itunes.delay(vendor.id, start_date - timedelta(x))

  if delay:
    # these are in the same queue, so this should happen after these ^
    finish_initial_ingestion.delay(user.id, start_date)
  else:
    really_finish_initial_ingestion.delay(user.id, start_date)


@celery_app.task(ignore_result=True, queue='itunes')
def ingest_new_sales_reports():
  # TODO(Anyone): Paging so we don't load all the vendors into memory all at once
  vendor_id_user_ids = ItunesConnectVendor.objects.filter(is_chosen=True).values_list('id', 'user_id')

  freshest_date = get_freshest_sales_report_date()
  for vendor_id, user_id in vendor_id_user_ids:
    _fetch_from_itunes.delay(vendor_id, freshest_date, notify=True)
    # This is to prevent hammering redis as we create thousands of new tasks
    # and chords there. In theory it will prevent this from happening:
    #   https://github.com/celery/celery/issues/1954
    time.sleep(0.1)


@celery_app.task(ignore_result=True, queue='itunesfetch')
def finish_initial_ingestion(user_id, requested_date):
  really_finish_initial_ingestion.apply_async(args=[user_id, requested_date], countdown=(60.0 * 4))


@celery_app.task(ignore_result=True, queue='itunes')
def really_finish_initial_ingestion(user_id, requested_date):
  user = User.objects.get(pk=user_id)
  user.set_flags(['has_sales_report_ready'])

  send_latest_report_for_user_subs.delay(user_id, requested_date)


def maybe_send_latest_report_to_user(user):
  # Delay this a bit to give the current transaction a second to finish.
  requested_date = get_freshest_sales_report_date()
  send_latest_report_for_user_subs.apply_async(args=[user.id, requested_date], countdown=5.0)


@celery_app.task(ignore_result=True, queue='itunes')
def send_latest_report_for_user_subs(user_id, requested_date):
  user = User.objects.get(pk=user_id)

  vendor = get_chosen_vendor_for_user(user)
  if not vendor:
    logging.info('No chosen vendor for user: %s', user.id)
    return

  status = report_status_for_vendor_date(vendor, requested_date)
  if status != REPORT_STATUS_AVAILABLE:
    logging.info('No report for user: %s', user.id)
    return

  # Do this atomically because we might be competing with another worker process.
  with transaction.atomic():
    last_report_date_matches = Q(latest_report_date__isnull=True) | Q(latest_report_date__lt=requested_date)
    subs = list(AppStoreSalesReportSubscription.objects.select_for_update().filter(last_report_date_matches, user=user, enabled=True))
    if not subs:
      return

    # Update subscriptions so we don't notify them again.
    AppStoreSalesReportSubscription.objects.filter(id__in=[s.id for s in subs]).update(latest_report_date=requested_date)

  app_metrics, total_metrics = get_sales_metrics(vendor, requested_date)
  if not app_metrics:
    logging.warn('No metrics for vendor id %s subscriptions (date: %s)', vendor.id, requested_date)
    return

  notifications = []
  email_messages = []

  for s in subs:
    n = AppStoreSalesReportNotification(user=s.user)

    if s.slack_channel_name or s.slack_url:
      message_dict = slack_sales_report_dict(app_metrics, total_metrics, requested_date)
      slack.post_message_to_slack_subscription(s, message_dict)

      if s.slack_url:
        n.slack_webhook = True
      else:
        n.slack_channel_name = s.slack_channel_name

    elif s.my_email or s.email:
      created_user = None
      if s.my_email:
        email = s.user.email
      else:
        created_user = s.user
        email = s.email

      unsub_url = unsubscribe_url_for_subscription(s)
      message = emails.create_sales_report_email(user, email, app_metrics, total_metrics, requested_date, unsub_url,
          created_user=created_user)
      email_messages.append(message)

      if s.my_email:
        n.my_email = True
      n.email = email

    else:
      logging.warn('Unsupported notification type for itunes notification: %s', s.id)

    notifications.append(n)

  if email_messages:
    emails.send_all(email_messages)

  if notifications:
    AppStoreSalesReportNotification.objects.bulk_create(notifications)


def unsubscribe_url_for_subscription(sub):
  base_url = '%ssales/unsubscribe/' % settings.SITE_URL
  token = crypto_hack.encrypt_object(
      {'time': time.time(), 'sub_id': sub.encrypted_id},
      settings.UNSUB_SUB_NOTIFY_SECRET)
  return urlutil.appendparams(base_url, token=token)


def subscription_from_unsubscribe_token(token):
  decrypted = crypto_hack.decrypt_object(token, settings.UNSUB_SUB_NOTIFY_SECRET)
  if not decrypted:
    return None
  if decrypted.get('time') < time.time() - (60 * 60 * 24 * 90):
    return None
  return AppStoreSalesReportSubscription.find_by_encrypted_id(decrypted.get('sub_id'))


def send_slack_subscription_configured_message(sub, force=False):
  slack_json = slack_enabled_json(sub.user.full_name)
  slack.post_message_to_slack_subscription(sub, slack_json, force=force)


def slack_enabled_json(user_name):
  return {
    'text': (
      "*Daily App Store sales reports have been added by %s. We will post download and sales summaries "
      "for your apps into this channel every morning.* "
      "Yesterday’s report will be posted as soon as your account is activated."
    ) % slack.escape(user_name),
    'icon_url': static('images/sales/icon.png'),
    'username': 'Sales Reporter',
  }


ATTACHMENTS_LIMIT = 19


def slack_sales_report_dict(app_sales_metrics, total_sales_metrics, report_date):
  attachments = []
  if total_sales_metrics:
    attachments.append(slack_sales_report_metrics_dict('Totals', total_sales_metrics))
  for app_metrics in app_sales_metrics[:ATTACHMENTS_LIMIT]:
    app, metrics = app_metrics['app'], app_metrics['metrics']
    attachment = slack_sales_report_metrics_dict(app.short_name, metrics, author_icon=app.public_small_icon)
    attachments.append(attachment)

  if len(app_sales_metrics) > ATTACHMENTS_LIMIT:
    remainder = len(app_sales_metrics) - ATTACHMENTS_LIMIT
    attachments.append({
      'text': '... and %d more' % remainder,
    })

  return {
    'username': 'Sales Reporter',
    'icon_url': static('images/icon_itunes_connect.png'),
    'text': 'Daily App Store Analytics for %s' % report_date.strftime('%B %d, %Y'),
    'attachments': attachments,
  }


def slack_sales_report_metrics_dict(author_name, metrics, author_icon=None):
  day_nonneg =  float(metrics['downloads']['day'].get('delta') or 0) >= 0
  week_nonneg = float(metrics['downloads'].get('week', {}).get('delta') or 0) >= 0

  slack_dict = {
    'color': 'good' if day_nonneg else 'danger',
    'author_name': author_name,
    'mrkdwn_in': ['fields'],
    'fields': [
      {
        'value': slack_field_value(metrics['downloads']['day']['requested'],
                   metrics['downloads']['day'].get('delta'),
                   metrics['downloads'].get('week', {}).get('delta'),
                   day_nonneg,
                   week_nonneg,
                   'downloads'
                 ),
        'short': 'TRUE',
      },
    ]
  }

  if author_icon:
    slack_dict['author_icon'] = author_icon

  if float(metrics['revenue'].get('week', {}).get('requested') or 0) > 0:
    day_nonneg = float(metrics['revenue']['day'].get('delta') or 0) >= 0
    week_nonneg = float(metrics['revenue'].get('week', {}).get('delta') or 0) >= 0
    slack_dict['fields'].append({
        'value': slack_field_value(metrics['revenue']['day']['requested'],
                   metrics['revenue']['day'].get('delta'),
                   metrics['revenue'].get('week', {}).get('delta'),
                   day_nonneg,
                   week_nonneg,
                   'revenue'
                 ),
        'short': 'TRUE',
    })

  return slack_dict


def slack_field_value(n, delta_day, delta_week, day_nonneg, week_nonneg, data_type):
  if delta_day:
    day_part = u'%s%s%% day' % ('+' if day_nonneg else '', delta_day)
  else:
    day_part = 'n/a day'

  if delta_week:
    week_part = u'%s%s%% week' % ('+' if week_nonneg else '', delta_week)
  else:
    week_part = 'n/a week'

  if data_type == 'revenue':
    return u'$%.2f\n_%s / %s_' % (n, day_part, week_part)
  else:
    return u'%i downloads\n_%s / %s_' % (n, day_part, week_part)


METRICS_DICT = {
  'downloads': {
    'week': {
      'requested': 0,
      'previous': 0,
    },
    'day': {
      'requested': 0,
      'previous': 0,
    },
  },
  'revenue': {
    'week': {
      'requested': 0,
      'previous': 0,
    },
    'day': {
      'requested': 0,
      'previous': 0,
    },
  },
}


def get_sales_metrics(vendor, requested_date, base_currency='usd'):
  if report_status_for_vendor_date(vendor, requested_date) != REPORT_STATUS_AVAILABLE:
    return None, None

  previous_date = requested_date - timedelta(1)

  requested_week_dates = [requested_date - timedelta(x) for x in range(7)]
  previous_week_dates = [requested_date - timedelta(x) for x in range(7, 14)]

  load_dates = requested_week_dates + previous_week_dates

  # There might NOT be a report for a given day (sales=0), so use the
  # non-failed report dates here that we know that we have fetched in order
  # to determine whether our data is good.
  dates_accounted_for = set(
      AppStoreSalesReportFetchedStatus.objects
      .filter(vendor=vendor, report_date__in=load_dates)
      .exclude(failed=True)
      .values_list('report_date', flat=True)
      .distinct()
  )

  reports = list(
    AppStoreSalesReport.objects
      .filter(vendor=vendor, end_date__in=load_dates)
      # Don't load the app name / promo code / category / version / etc. here
      .only('app_id', 'developer_proceeds', 'proceeds_currency', 'units', 'end_date', 'product_type_identifier')
  )

  total_sales_metrics = copy.deepcopy(METRICS_DICT)
  app_sales_metrics = {}

  currency_conversions = conversion_dict_for_currency(base_currency) or {}

  for report in reports:
    app_id = report.app_id
    if app_id not in app_sales_metrics:
      app_sales_metrics[app_id] = copy.deepcopy(METRICS_DICT)

    revenue = float(report.developer_proceeds or 0)
    if report.proceeds_currency != base_currency:
      if report.proceeds_currency in currency_conversions:
        revenue = revenue / currency_conversions[report.proceeds_currency]
      else:
        logging.error('Itunes Connect Error - currency conversion not found: %s -> %s', report.proceeds_currency, base_currency)
        revenue = 0

    # developer_proceeds is the unit price. units is a decimal.
    revenue *= float(report.units)

    if revenue > 0:
      if report.end_date in requested_week_dates:
        app_sales_metrics[app_id]['revenue']['week']['requested'] += revenue
        total_sales_metrics['revenue']['week']['requested'] += revenue
        if report.end_date == requested_date:
          app_sales_metrics[app_id]['revenue']['day']['requested'] += revenue
          total_sales_metrics['revenue']['day']['requested'] += revenue
        if report.end_date == previous_date:
          app_sales_metrics[app_id]['revenue']['day']['previous'] += revenue
          total_sales_metrics['revenue']['day']['previous'] += revenue
      else:
        app_sales_metrics[app_id]['revenue']['week']['previous'] += revenue
        total_sales_metrics['revenue']['week']['previous'] += revenue

    if report.is_download:
      downloads = int(report.units)
      if report.end_date in requested_week_dates:
        app_sales_metrics[app_id]['downloads']['week']['requested'] += downloads
        total_sales_metrics['downloads']['week']['requested'] += downloads
        if report.end_date == requested_date:
          app_sales_metrics[app_id]['downloads']['day']['requested'] += downloads
          total_sales_metrics['downloads']['day']['requested'] += downloads
        if report.end_date == previous_date:
          app_sales_metrics[app_id]['downloads']['day']['previous'] += downloads
          total_sales_metrics['downloads']['day']['previous'] += downloads
      else:
        app_sales_metrics[app_id]['downloads']['week']['previous'] += downloads
        total_sales_metrics['downloads']['week']['previous'] += downloads

  if requested_date not in dates_accounted_for:
    logging.warn('Requested date not in dates accounted for, yet status was available')
    return None, None

  # We might not have the full week -- if we don't have the full week,
  # we can't show the data because it will be incorrect.
  has_requested_week_data = all(map(lambda d: d in dates_accounted_for, requested_week_dates))
  if not has_requested_week_data:
    del total_sales_metrics['downloads']['week']
    del total_sales_metrics['revenue']['week']
    for app_id in app_sales_metrics:
      del app_sales_metrics[app_id]['downloads']['week']
      del app_sales_metrics[app_id]['revenue']['week']

  has_previous_day_data = previous_date in dates_accounted_for
  has_previous_week_data = all(map(lambda d: d in dates_accounted_for, previous_week_dates))

  if has_previous_day_data:
    total_daily_dls = total_sales_metrics['downloads']['day']
    total_daily_dls['delta'] = formatted_delta(total_daily_dls['requested'], total_daily_dls['previous'])

    total_daily_rev = total_sales_metrics['revenue']['day']
    total_daily_rev['delta'] = formatted_delta(total_daily_rev['requested'], total_daily_rev['previous'])

  if has_requested_week_data and has_previous_week_data:
    total_weekly_dls = total_sales_metrics['downloads']['week']
    total_weekly_dls['delta'] = formatted_delta(total_weekly_dls['requested'], total_weekly_dls['previous'])

    total_weekly_rev = total_sales_metrics['revenue']['week']
    total_weekly_rev['delta'] = formatted_delta(total_weekly_rev['requested'], total_weekly_rev['previous'])

  for app_id in app_sales_metrics:
    if has_previous_day_data:
      daily_dls = app_sales_metrics[app_id]['downloads']['day']
      daily_dls['delta'] = formatted_delta(daily_dls['requested'], daily_dls['previous'])

      daily_rev = app_sales_metrics[app_id]['revenue']['day']
      daily_rev['delta'] = formatted_delta(daily_rev['requested'], daily_rev['previous'])

    if has_requested_week_data and has_previous_week_data:
      weekly_dls = app_sales_metrics[app_id]['downloads']['week']
      weekly_dls['delta'] = formatted_delta(weekly_dls['requested'], weekly_dls['previous'])

      weekly_rev = app_sales_metrics[app_id]['revenue']['week']
      weekly_rev['delta'] = formatted_delta(weekly_rev['requested'], weekly_rev['previous'])

  apps_by_id = {a.id: a for a in AppStoreApp.objects.filter(id__in=app_sales_metrics.keys())}
  app_sales_metrics_list = []
  for app_id in app_sales_metrics:
    metrics = app_sales_metrics[app_id]
    app = apps_by_id[app_id]
    appstore_app_info.decorate_app(app, app.app_info_countries[0])
    app_sales_metrics_list.append({'app': app, 'metrics': metrics})
  app_sales_metrics_list.sort(key=lambda a: a['metrics']['downloads']['day']['requested'], reverse=True)

  if len(app_sales_metrics_list) == 1:
    total_sales_metrics = None

  return app_sales_metrics_list, total_sales_metrics

