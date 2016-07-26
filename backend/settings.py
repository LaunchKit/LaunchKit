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



#
# LK Configuration
#

# Set this S3 bucket name if you want to upload screenshot bundles to S3.

BUNDLES_S3_BUCKET_NAME = ""

# This should be an IAM role with read & write access to the BUNDLES_S3_BUCKET_NAME bucket.

READWRITE_S3_ACCESS_KEY_ID = ""
READWRITE_S3_SECRET_ACCESS_KEY = ""

# This should be an IAM role with readonly access to the BUNDLES_S3_BUCKET_NAME bucket.

READONLY_S3_ACCESS_KEY_ID = ""
READONLY_S3_SECRET_ACCESS_KEY = ""

# If you want email to work, configure an SMTP server here.

EMAIL_SMTP_HOST = None # eg. "smtp.sendgrid.com"
EMAIL_SMTP_USER = None
EMAIL_SMTP_PASSWORD = None
EMAIL_FROM_DOMAIN = "yoursite.com"


# If you want Review Monitor & Sales Reporter to post to Slack,
# create a Slack app at: https://api.slack.com/slack-apps
# and then add your keys here.

SLACK_CLIENT_ID = ""
SLACK_CLIENT_SECRET = ""

# If you want Review Monitor to post to Twitter,
# create a Twitter app at: https://apps.twitter.com/
# and then add your ID and secret key here.

TWITTER_APP_KEY = ""
TWITTER_APP_SECRET = ""

# If you post reviews from this instance of LK publicly and want to generate
# friendly review previews, create a URL2PNG account: https://www.url2png.com/
# and then add your URL key and secret here.

URL2PNG_URL_KEY = ""
URL2PNG_SECRET_KEY = ""

# If you configure an actual CNAME website host, set your hosting domain here.
# (This webserver is running on localhost:9105 by default.)

HOSTED_WEBSITE_CNAME = "domains.yoursite.com"

# If you end up hosting this instance of LK publicly or opening it up to a
# corporate network, set your SITE_URL to the user-facing address. (This is
# used for generating links in emails & such.)

SITE_URL = "http://localhost:9100/"

#
# The path to the LaunchKit API server, from the perspective of a client.
#

API_URL = "http://localhost:9101/"

# Similar to SITE_URL, if you end up actually creating an App Engine host for
# your images, you can set that URL here. (eg. "https://foobar.appspot.com")
# Or, if you host this in an internal network (not localhost), set the
# user-facing address here.

#
# IMPORTANT: If you modify this value, also modify the value in
# skit/settings.js to the same value.
#
APP_ENGINE_PHOTOS_UPLOAD_BASE_PATH = "http://localhost:9102"

#
# SECRETS
#
# These encrypt various things on this website.
# Change these to random hex strings of the same length.
#
# TODO(you): Change these to random strings, using: https://www.random.org/strings/
#

UNSUBSCRIBE_URL_SECRET = '00000000000000000000000000000000' # must be 32 hex chars
BETA_LINK_SECRET = '00000000000000000000000000000000' # must be 32 hex chars
UNSUB_SUB_NOTIFY_SECRET = '00000000000000000000000000000000' # must be 32 hex chars

ENCRYPTED_ID_KEY_IV  = '0000000000000000' # must be 16 hex chars

COOKIE_SECRET_KEY = '00000000000000000000000000000000' # arbitrary secret

APP_ENGINE_HEADER_SECRET = '00000000000000000000000000000000' # arbitrary, but must match secret in gae/ directory







#
#
# __          __     _____  _   _ _____ _   _  _____
# \ \        / /\   |  __ \| \ | |_   _| \ | |/ ____|
#  \ \  /\  / /  \  | |__) |  \| | | | |  \| | |  __
#   \ \/  \/ / /\ \ |  _  /| . ` | | | | . ` | | |_ |
#    \  /\  / ____ \| | \ \| |\  |_| |_| |\  | |__| |
#     \/  \/_/    \_\_|  \_\_| \_|_____|_| \_|\_____|
#
# It gets pretty gnarly down here; proceed with caution.
#
# Internal configuration below; only edit if you're feeling adventurous.
# This should only be edited if you are changing the hosting environment in a nontrivial way.
#
#

import os
import os.path
import sys
from datetime import timedelta

from celery.schedules import crontab

# Set default encoding for loading strings as utf-8.
reload(sys)
sys.setdefaultencoding("utf-8")



#
# GLOBAL SETTINGS
#

IS_PRODUCTION = False
IS_TESTING = False

DEBUG_SLOW_REQUESTS = False

ROOT_PATH = os.path.abspath(os.path.dirname(__file__))

DEBUG = not IS_PRODUCTION
TEMPLATE_DEBUG = not IS_PRODUCTION

SECRET_KEY = COOKIE_SECRET_KEY

# This is required for login() to work.
AUTH_USER_MODEL = 'lk.User'

TIME_ZONE = 'UTC'
LANGUAGE_CODE = 'en-us'
# Setting these are an optimization to keep Django from loading various
# i18n/l10n machinery.
USE_I18N = False
USE_L10N = False
USE_TZ = False

ROOT_URLCONF = 'backend.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'backend.wsgi.application'


#
# SITE-SPECIFIC SETTINGS
#

if not SITE_URL.endswith('/'):
  SITE_URL += '/'

if not API_URL.endswith('/'):
  API_URL += '/'

TWITTER_CONSUMER_KEY = TWITTER_APP_KEY
TWITTER_CONSUMER_SECRET = TWITTER_APP_SECRET

# Only checked in production -- list of acceptable serving urls.
ALLOWED_HOSTS = ['*']


#
# DATABASE
#


POSTGRES_ENGINE = 'django.db.backends.postgresql_psycopg2'
POSTGRES_OPTIONS = {}


DATABASES = {
  'default': {
    'ENGINE': POSTGRES_ENGINE,

    'NAME': 'lk',
    'USER': 'vagrant',
    'PASSWORD': '',
    'HOST': 'localhost',
    'PORT': '5432',

    'ATOMIC_REQUESTS': True,

    # These are handled by django_db_geventpool itself in production.
    'CONN_MAX_AGE': 0,

    'OPTIONS': POSTGRES_OPTIONS,
  }
}


#
# REDIS
#

REDIS_URL = "redis://localhost:6379/0"


#
# APP ENGINE PHOTOS
#

APP_ENGINE_PHOTOS_UPLOAD_BASE_PATH = APP_ENGINE_PHOTOS_UPLOAD_BASE_PATH.rstrip('/')


#
# CELERY
#

BROKER_URL = REDIS_URL

# NOTE: This is supposed to be larger than the largest ETA/countdown of any
# task we use in the system including retries.
BROKER_TRANSPORT_OPTIONS = {'visibility_timeout': 60 * 60 * 12}

CELERY_RESULT_BACKEND = REDIS_URL

# This corresponds to kombu.connection.Connection:ensure_connection keyword arguments.
# Yes, really. I know. So crazy.
CELERY_TASK_PUBLISH_RETRY_POLICY = {
  'max_retries': 3,
}

# 1 hour.
CELERY_TASK_RESULT_EXPIRES = 60 * 60

# 10-minute task limit.
CELERYD_TASK_SOFT_TIME_LIMIT = 60 * 10

CELERY_ACCEPT_CONTENT = ['pickle', 'json']

CELERY_TIMEZONE = 'US/Pacific'

CELERYBEAT_SCHEDULE = {
  'delete-photos': {
    'task': 'backend.lk.logic.gae_photos.clean_up_deleted_images',
    'schedule': timedelta(minutes=10),
  },

  'expire-photos': {
    'task': 'backend.lk.logic.gae_photos.clean_up_expired_images',
    'schedule': timedelta(minutes=10),
  },

  'assign-bundle-images': {
    'task': 'backend.lk.logic.screenshot_bundler.assign_bundle_images',
    'schedule': timedelta(minutes=2),
  },

  'review-readiness': {
    'task': 'backend.lk.logic.appstore_review_ingestion.maybe_send_reviews_ready_emails',
    'schedule': timedelta(minutes=1),
  },
  'info-ingestion': {
    'task': 'backend.lk.logic.appstore_app_info.maybe_ingest_app_info',
    # TODO(Taylor): Bump this up in real life.
    'schedule': timedelta(seconds=30),
  },

  'sales-report-ingestion': {
    'task': 'backend.lk.logic.itunes_connect.ingest_new_sales_reports',
    # daily at 6:30 AM US/Pacific time
    'schedule': crontab(minute=30, hour=6),
  },

  # SDK user info.

  'process-sessions': {
    'task': 'backend.lk.logic.sessions.process_session_data',
    'schedule': timedelta(seconds=DEBUG and 60 or 5),
  },
  'process-dirty-user-labels': {
    'task': 'backend.lk.logic.session_user_labels.process_dirty_sdk_user_labels',
    'schedule': timedelta(minutes=1),
  },
  'process-weekly-inactive-labels': {
    'task': 'backend.lk.logic.session_user_labels.process_weekly_inactive_sessions',
    'schedule': timedelta(seconds=95),
  },
  'record-tracking-stats': {
    'task': 'backend.lk.logic.session_user_labels.save_hourly_label_counts',
    'schedule': crontab(minute=5),
  },
  'process-labels-periodically': {
    'task': 'backend.lk.logic.session_user_labels.process_sdkuser_labels_periodically',
    'schedule': timedelta(minutes=1),
  },
}


#
# S3
#

_AWS_BUCKET_FORMAT = '%s.s3.amazonaws.com'

BUNDLES_S3_BUCKET_NAME_HOST = _AWS_BUCKET_FORMAT % BUNDLES_S3_BUCKET_NAME


#
# EMAIL
#

if EMAIL_SMTP_HOST:
  EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

  EMAIL_HOST = EMAIL_SMTP_HOST
  EMAIL_USER = EMAIL_SMTP_USER
  EMAIL_PASSWORD = EMAIL_SMTP_PASSWORD
  EMAIL_PORT = 587
  EMAIL_USE_TLS = True

else:
  # If no email host/user is provided, fall back to console output.
  EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'


#
# SECURE REDIRECT (http:// -> https://)
#


USE_X_FORWARDED_HOST = True


# Helps us identify SSL on EC2/Heroku/etc.
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https',)


UNDESIRABLE_DOMAINS = {
  # TODO: Add eg. 'www.foo.com': 'foo.com', to redirect away from www.
}

# TODO: Add eg. 'foo.com' to redirect from http -> https for that domain
REDIRECT_INSECURE_DOMAINS = set([])


#
# OAUTH APPS
#

class OAuthClient(object):
  def __init__(self, client_id, description, secret):
    self.client_id = client_id
    self.description = description
    self.secret = secret

OAUTH_CLIENT_WEB = 'launchkit-skit'

OAUTH_CLIENTS = [
  OAuthClient('launchkit-skit', 'Web', '5ZP672EiPfWHLsoDPitlcTE3CKQnE4ynVjgNKBx4EQNoi'),
  OAuthClient('launchkit-test', 'Test Client', 'PftJjBQo91T64y7ps0XKtSd1bBAnIDFRQBfn5zVKtZBY7'),

  # OAuthClient('', '', 'w5XLxTZcQA1QbDuRPrFFtp9KfvbiyWQHON4O0V5NKWPnw'),
  # OAuthClient('', '', 'KSRfsz4XtZraAA6utjZ7642dLvIMQJGwE1byZe9zhKmqz'),
  # OAuthClient('', '', '9g5GMzGnPXo3fbv7vRGIuKyyOB5PaXbbszbkWWE87pFDB'),
  # OAuthClient('', '', '5Ezx246IHc0OqpUGq9UYNFtx4au3CvPyuB3SUeMmkMJ5y'),
  # OAuthClient('', '', 'GyulQYSpN1jMohWvgdJEXnHELGIwrTEhYeip5TquwJooA'),
  # OAuthClient('', '', 'LFlznGmSEhEltxEIN6O40hzXXuo1BQROFbMXm799NyEk5'),
  # OAuthClient('', '', 'KqKrKSxo4UVeiVuCRIgiTsGFs9S9qBqAhYWdHR3xB8skV'),
  # OAuthClient('', '', 'bHPFcha0cInnHw4cjfBCWV2if2dgJI6VADsKnxJ6kJXZF'),
  # OAuthClient('', '', 'w18YGuGzoKYnx6A8ehuI1bdOudl4fBu0sbOYYe8gWeXOK'),
  # OAuthClient('', '', 'iHOWUqATQHR4Yke1wooVzULa03xtGEKEVBN83D0Ms98xz'),
  # OAuthClient('', '', 'W5HhSKRQPilXC7DE6FnLoTPmyggyDg798aDXjxRRjgZWh'),
  # OAuthClient('', '', 'HQbIUvu5aXMw5169oDLNvqSDyulGNL6jjQRekb1RdCJlj'),
  # OAuthClient('', '', 'myEjrw6Ooe1cvQLRDP8RiC6XyuUb4TdzdI9f6QXqkq8fp'),
]

OAUTH_CLIENT_CHOICES = [(client.client_id, client.description) for client in OAUTH_CLIENTS]
OAUTH_CLIENTS_BY_ID = dict((client.client_id, client) for client in OAUTH_CLIENTS)


OAUTH_SCOPE_READONLY = 'readonly'
OAUTH_SCOPE_READWRITE = 'readwrite'

OAUTH_SCOPE_CHOICES = [
  (OAUTH_SCOPE_READONLY, 'Read-Only'),
  (OAUTH_SCOPE_READWRITE, 'Read/Write'),
]


OAUTH_GRANT_PASSWORD =  'password'
OAUTH_GRANT_TOKEN =     'urn:launchkit.io:oauth2:grant-type:oauthtoken'

OAUTH_GRANT_CHOICES = [
  (OAUTH_GRANT_PASSWORD,  'Password Authentication'),
  # Extension grant: http://tools.ietf.org/html/rfc6749#section-4.5
  # (OAUTH_GRANT_TOKEN,     'Existing Token'),
]


#
# STATIC FILES STORAGE
#


STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
STATIC_URL = '/static/'

STATICFILES_DIRS = (
  os.path.join(os.path.dirname(__file__), 'site_media'),
)

STATICFILES_FINDERS = (
  'django.contrib.staticfiles.finders.FileSystemFinder',
  'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

STATIC_ROOT = os.path.join(ROOT_PATH, 'static')


#
# TEMPLATES
#


TEMPLATE_LOADERS = (
  'django.template.loaders.filesystem.Loader',
  'django.template.loaders.app_directories.Loader',
)

TEMPLATE_CONTEXT_PROCESSORS = (
  'django.core.context_processors.request',
)

TEMPLATE_DIRS = (
  ROOT_PATH + '/templates',
)


#
# LOGGING
#

LOGGING = {
  'version': 1,
  'disable_existing_loggers': False,
  'filters': {
    'require_debug_false': {
      '()': 'django.utils.log.RequireDebugFalse'
    }
  },
  'formatters': {
      'simple': {
          'format': '[%(levelname)s] %(message)s'
      },
  },
  'handlers': {
    'console': {
      'level': 'INFO',
      'class':'logging.StreamHandler',
      'stream': sys.stdout,
      'formatter': 'simple',
    }
  },
  'loggers': {
    'django.request': {
      'handlers': ['console',],
      'level': 'ERROR',
      'propagate': True,
    },
    'django.db.backends': {
      'handlers': ['console',],
      'level': 'INFO',
      'propagate': False,
    },
    '': {
      'handlers': ['console'],
      'propagate': True,
      'level': 'DEBUG',
    }
  },
}


#
# CACHE CONFIGURATION
#

CACHES = {
  'default': {
    'BACKEND': "django.core.cache.backends.dummy.DummyCache",
    'LOCATION': None,
    'TIMEOUT': 24 * 60 * 60,
  },
  'staticfiles': {
    'BACKEND': "django.core.cache.backends.dummy.DummyCache",
  }
}


#
# MIDDLEWARE AND INSTALLED APPS
#

MIDDLEWARE_CLASSES = (
  'backend.middleware.SetRemoteAddrFromForwardedFor',
  'backend.middleware.SecureRequiredMiddleware',

  'django.middleware.common.CommonMiddleware',
  'django.middleware.http.ConditionalGetMiddleware',

  'backend.middleware.JSONPostMiddleware',

  'django.middleware.gzip.GZipMiddleware',

  'backend.lk.oauth_middleware.OAuthAuthenticationMiddleware',
)

INSTALLED_APPS = [
  'django.contrib.staticfiles',
  'django.contrib.humanize',
  'backend.lk',
]
