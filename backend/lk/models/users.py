# -*- coding: utf-8 -*-
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

from bitfield import BitField
from django.contrib.auth.models import AbstractBaseUser
from django.contrib.auth.models import UserManager
from django.db import models
from django.db.models import F

from backend.lk.models.apimodel import APIModel
from backend.lk.models.email_tokens import EmailToken
from backend.util import hstore_field


class User(AbstractBaseUser, APIModel):
  # Set this to None to get the default key.
  ENCRYPTED_ID_KEY_TOKEN = None

  USERNAME_FIELD = 'email'
  REQUIRED_FIELDS = ['first_name', 'last_name']

  first_name = models.CharField(max_length=30, blank=True, null=True)
  last_name = models.CharField(max_length=30, blank=True, null=True)

  email = models.EmailField(null=True, unique=True)
  phone = models.CharField(max_length=30, null=True, unique=True)

  is_staff = False
  is_active = True
  is_superuser = models.BooleanField(default=False)

  date_joined = models.DateTimeField(auto_now_add=True)

  delete_time = models.DateTimeField(null=True)

  # Random user attributes we find out.
  data = hstore_field.HStoreField(null=True)

  app_versions = hstore_field.HStoreField(null=True)

  flags = BitField(default=0, flags=[
    'has_unverified_email',        # 0

    'unsubscribed_from_email',     # 1

    'any_reviews_ready',           # 2
    'any_reviews_pending',         # 3

    'has_reviews_onboarded',       # 4

    'beta_optin',                  # 5

    'has_review_monitor',          # 6
    'has_review_monitor_tweets',   # 7
    'has_screenshot_builder',      # 8
    'has_sales_monitor',           # 9

    'has_sales_report_ready',      # 10
    'has_sales_onboarded',         # 11

    'has_websites',                # 12

    'sent_beta_optin_email',       # 13

    'has_super_users',             # 14

    'has_config',                  # 15

    'has_sent_tracking_data',      # 16
  ])

  objects = UserManager()


  def set_unset_flags(self, set_flags=None, unset_flags=None):
    if not (set_flags or unset_flags):
      return

    flags_to_set_value = 0
    for flag in (set_flags or []):
      flags_to_set_value |= getattr(User.flags, flag)
      setattr(self.flags, flag, True)

    flags_to_unset_value = 0
    for flag in (unset_flags or []):
      flags_to_unset_value |= getattr(User.flags, flag)
      setattr(self.flags, flag, False)

    User.objects.filter(pk=self.id).update(flags=F('flags').bitor(flags_to_set_value).bitand(~flags_to_unset_value))
    self.invalidate_cache()

  def set_flags(self, set_flags):
    self.set_unset_flags(set_flags=set_flags)

  def unset_flags(self, unset_flags):
    self.set_unset_flags(unset_flags=unset_flags)

  def mark_has_unverified_email(self, marked=True):
    if bool(self.flags.has_unverified_email) == marked:
      return

    if marked:
      self.set_flags(['has_unverified_email'])
    else:
      self.unset_flags(['has_unverified_email'])

  def has_perm(self, perm, obj=None):
    return self.is_superuser

  def has_module_perms(self, app_label):
    return self.is_superuser

  @property
  def _names(self):
    return [n for n in (self.first_name, self.last_name) if n]

  @property
  def initials(self):
    names = self._names
    if names:
      initials = [n[:1] for n in names]
    else:
      if self.email:
        initials = [self.email[:1]]
    return (''.join(initials)).upper()

  @property
  def full_name(self):
    name = ' '.join(self._names)
    if name:
      return name
    if self.email:
      return self.email

  @property
  def medium_name(self):
    names = self._names
    if len(names) == 2:
      return '%s %s.' % (names[0], names[1][:1])
    if len(names) == 1:
      return names[0]
    if self.email:
      return self.email[:10] + '...'
    return None

  @property
  def short_name(self):
    names = self._names
    if len(names):
      return names[0]
    if self.email:
      return self.email[:8] + '...'
    return None

  def names_dict(self, first_last=False):
    names = {
      'short': self.short_name,
      'full': self.full_name,
      'initials': self.initials,
    }
    if first_last:
      names['first'] = self.first_name
      names['last'] = self.last_name
    return names

  #
  # CACHING
  #

  @classmethod
  def cache_key_for_id(cls, user_id):
    return 'lk_user:%d' % user_id

  #
  # HANDY PROPERTIES
  #


  @property
  def small_avatar_url(self):
    # FIXME(Taylor)
    # if self.gae_avatar_url:
    #   return self.gae_avatar_url + '=s200-c'
    return None

  @property
  def large_avatar_url(self):
    # FIXME(Taylor)
    # if self.gae_avatar_url:
    #   return self.gae_avatar_url + '=s640-c'
    return None

  @property
  def twitter_handles(self):
    return [x.handle for x in self.twitter_access_tokens_set.filter(invalidated_time__isnull=True)]

  @property
  def products_list(self):
    products = []
    if self.flags.has_review_monitor:
      products.append('reviews')
    if self.flags.has_screenshot_builder:
      products.append('screenshots')
    if self.flags.has_sales_monitor:
      products.append('sales')
    if self.flags.has_websites:
      products.append('websites')
    if self.flags.has_super_users:
      products.append('super_users')
    if self.flags.has_config:
      products.append('config')
    return products

  #
  # JSON
  #

  def to_dict(self):
    response = {
      'id': self.encrypted_id,

      'avatarUrls': {
        'small': self.small_avatar_url,
        'large': self.large_avatar_url,
      },

      'names': self.names_dict(first_last=True),

      'createTime': self.date_to_api_date(self.date_joined),
    }

    if self.email:
      response['email'] = self.email
      if self.flags.has_unverified_email:
        response['hasUnverifiedEmail'] = True

    if self.flags.any_reviews_pending and not self.flags.any_reviews_ready:
      response['reviewsPending'] = True

    if self.flags.has_sales_report_ready:
      response['salesReportReady'] = True


    # TODO(Taylor): Generalize this somehow?
    if not self.flags.has_reviews_onboarded:
      response['needsReviewsOnboarding'] = True
    if not self.flags.has_sales_onboarded:
      response['needsSalesOnboarding'] = True

    if self.flags.beta_optin:
      response['beta'] = True

    response['products'] = self.products_list

    return response

  def to_minimal_dict(self):
    response = {
      'id': self.encrypted_id,
      'avatarUrls': {
        'small': self.small_avatar_url,
        'large': self.large_avatar_url,
      },
      'names': self.names_dict(),
    }
    return response

  def __unicode__(self):
    return self.full_name


class UserEmail(APIModel):
  email = models.EmailField(unique=True)
  user = models.ForeignKey(User, related_name='emails_set', on_delete=models.DO_NOTHING)

  primary = models.BooleanField(default=True)
  verified = models.BooleanField(default=False)
  source_token = models.ForeignKey(EmailToken, null=True, on_delete=models.DO_NOTHING)
  create_time = models.DateTimeField(auto_now_add=True)

  def to_dict(self):
    return {
      'email': self.email,
      'verified': self.verified,
      'primary': self.primary,
      'createTime': self.date_to_api_date(self.create_time),
    }
