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
import time
from datetime import datetime

from django.conf import settings

from backend.lk.logic import crypto_hack
from backend.lk.logic import emails
from backend.lk.models import User
from backend.lk.models import UserEmail
from backend.lk.models import EmailToken
from backend.util import urlutil
from backend import celery_app


#
# FETCHING
#


def get_user_by_email(email, only_verified=False, for_update=False):
  if not email:
    return None

  user_emails = get_user_emails(email)
  if only_verified:
    user_emails = [e for e in user_emails if e.verified]

  if not user_emails:
    return None

  user_email = user_emails[0]
  if for_update:
    return User.objects.select_for_update().get(pk=user_email.user_id)
  else:
    return user_email.user


def get_user_emails(email):
  email = email.lower()
  if email.endswith('@gmail.com'):
    user_emails = UserEmail.objects.raw("""
      SELECT * FROM lk_useremail WHERE
          REPLACE(email, '.', '') = %s
    """, [email.replace('.', '')])
  else:
    user_emails = UserEmail.objects.filter(email=email.lower()).select_related('user')
  return list(user_emails)


def email_is_reassignable(email):
  # Primary and verified email addresses can't be snatched away without
  # merging accounts or at least verifying.
  matching_emails = get_user_emails(email)
  nonreassignable = [e for e in matching_emails if (e.primary or e.verified)]
  return len(nonreassignable) == 0


def get_user_by_email_token(raw_token):
  tokens = EmailToken.objects.filter(token=raw_token)
  if not tokens:
    return None

  return get_user_by_email(tokens[0].email)


def get_verified_emails(user):
  user_emails = UserEmail.objects.filter(user=user, verified=True)
  return [email.email for email in user_emails]


def get_unverified_emails(user):
  user_emails = UserEmail.objects.filter(user=user, verified=False)
  return [email.email for email in user_emails]


def create_user(first_name, last_name, email=None, verified_email=False, password=None):
  if not email:
    raise ValueError('No email provided')

  user = User()

  user.first_name = first_name
  user.last_name = last_name

  if not password:
    user.set_unusable_password()
  else:
    user.set_password(password)

  user.save()

  if email:
    success = associate_user_with_email(user, email, verified=verified_email, send_email=False)
    if not success:
      user.delete()
      return None

  send_welcome_email.apply_async(args=[user.id], countdown=60.0)

  return user


@celery_app.task(ignore_result=True)
def send_welcome_email(user_id):
  user = User.get_cached(user_id)
  if not user:
    # Deleted, rollbacked transaction, etc.
    return

  unsubscribe_url = generate_user_unsubscribe_url(user, 'unsubscribed_from_email')

  verify_url = None
  if user.flags.has_unverified_email:
    verify_url = verification_url_for_user_email(user, user.email)

  email = emails.create_welcome_email(user, verify_url, unsubscribe_url)
  emails.send_all([email])


#
# EDIT USER
#

# Subset of the flags that can be edited by users.
BETA_OPTIN_FLAG = 'beta_optin'
USER_EDITABLE_USER_FLAGS = [
  'unsubscribed_from_email',

  'has_reviews_onboarded',
  'has_sales_onboarded',

  BETA_OPTIN_FLAG,
]


def update_user_flags(user, flags):
  flags_to_set = []
  flags_to_unset = []
  for flag in set(USER_EDITABLE_USER_FLAGS) & set(flags.keys()):
    if flags[flag]:
      if not getattr(user.flags, flag):
        flags_to_set.append(flag)
    else:
      if getattr(user.flags, flag):
        flags_to_unset.append(flag)
  user.set_unset_flags(set_flags=flags_to_set, unset_flags=flags_to_unset)


#
# UNSUBSCRIBE LINKS
#


def generate_user_unsubscribe_url(user, flag_name):
  if flag_name and flag_name not in USER_EDITABLE_USER_FLAGS:
    raise ValueError('Invalid flag_name %s', flag_name)

  encrypted_token = crypto_hack.encrypt_object({'user_id': user.id, 'flag_name': flag_name},
      settings.UNSUBSCRIBE_URL_SECRET)

  url = '%saccount/unsubscribe/' % settings.SITE_URL
  return urlutil.appendparams(url, token=encrypted_token)


def unsubscribe_with_token(token):
  user_dict = crypto_hack.decrypt_object(token, settings.UNSUBSCRIBE_URL_SECRET)
  if not user_dict:
    return False

  user = User.get_cached(user_dict['user_id'])
  flag = user_dict['flag_name']

  if flag not in USER_EDITABLE_USER_FLAGS:
    logging.warn('WTF? uneditable flag: %s for user: %s', flag, user.id)
    return False

  if flag.startswith('enable') or flag.endswith('optin'):
    unsubscribed_value = False
  else:
    unsubscribed_value = True

  update_user_flags(user, {flag: unsubscribed_value})

  return True


#
# ASSOCIATIONS
#


def associate_user_with_email(user, email, verified=False, send_email=True):
  email = email.lower()

  email_objs = get_user_emails(email)
  if email_objs:
    email_obj = email_objs[0]
    if email_obj.user_id == user.id:
      if verified:
        return verify_email(user, email)
      else:
        return email_obj

    if email_obj.primary or email_obj.verified:
      # There is an email, but it doesn't belong to this user.
      return None

    # Someone else's non-primary address can just be disassociated.
    email_obj.delete()

  if not user.email:
    primary = True
    user.email = email.lower()
    user.save()
  else:
    primary = False

  email_obj = UserEmail(email=email.lower(), user=user, primary=primary, verified=verified)
  email_obj.save()

  if not verified:
    user.mark_has_unverified_email()
    if send_email:
      _send_verification_email(user, email=email)

  return email_obj


def disassociate_user_with_email(user, email):
  email_objs = UserEmail.objects.filter(user=user)
  if not email_objs:
    return False

  email_obj = [e for e in email_objs if email == e.email]
  if not email_obj:
    return False
  email_obj = email_obj[0]

  if len(email_objs) == 1:
    # Cannot delete the last email
    return False

  if email_obj.primary and len(email_objs) > 1:
    other_email_objs = [e for e in email_objs if e.email != email]
    make_email_primary(user, other_email_objs[0].email)

  if email == user.email:
    user.email = None
    user.save()

  email_obj.delete()
  return True


#
# VERIFICATION
#


def verify_email_from_user_token(user, verification_token):
  email_token = EmailToken.objects.filter(token=verification_token)
  if not email_token:
    return False
  email_token = email_token[0]

  if not verify_email(user, email_token.email, source_token=email_token):
    return False

  if not email_token.redemption_time:
    email_token.redemption_time = datetime.now()
    email_token.save()

  return True


def verify_email_from_token(verification_token):
  email_token = EmailToken.objects.filter(token=verification_token)
  if not email_token:
    return False
  email_token = email_token[0]

  user = get_user_by_email(email_token.email)
  if not user:
    return False

  return verify_email_from_user_token(user, verification_token)


def verify_email(user, email, source_token=None):
  user_emails = get_user_emails(email)
  if not user_emails:
    return None
  user_email = user_emails[0]

  if user_email.user_id != user.id:
    return None

  if not user_email.verified:
    user_email.verified = True
    user_email.source_token = source_token
    user_email.save()

  # If the user has no more unverified addresses...
  if UserEmail.objects.filter(user=user, verified=False).count() == 0:
    user.mark_has_unverified_email(False)

  return user_email


def make_email_primary(user, new_primary_email):
  try:
    UserEmail.objects.get(user=user, email=new_primary_email)
  except UserEmail.DoesNotExist:
    return False

  UserEmail.objects.filter(user_id=user.id).update(primary=False)
  UserEmail.objects.filter(user_id=user.id, email=new_primary_email).update(primary=True)
  user.email = new_primary_email
  user.save(update_fields=['email'])

  return True


#
# RESET
#


def request_reset_password_email(email):
  user = get_user_by_email(email)
  if not user:
    return False

  email_token = EmailToken(kind=EmailToken.KIND_RESET_PASSWORD, email=email.lower())
  email_token.save()

  reset_password_url = '%saccount/reset/finish/' % settings.SITE_URL
  reset_password_url = urlutil.appendparams(reset_password_url,
      token=email_token.token, email=email_token.email)

  emails.send_reset_password_email(user, reset_password_url)

  return True


def verification_url_for_user_email(user, email):
  email_token = EmailToken(kind=EmailToken.KIND_VERIFY_EMAIL, email=email)
  email_token.save()

  email_verification_url = '%saccount/verify/' % settings.SITE_URL
  email_verification_url = urlutil.appendparams(email_verification_url,
      token=email_token.token)

  return email_verification_url


def request_verification_email(email):
  email_objects = get_user_emails(email)
  if not email_objects or email_objects[0].verified:
    return False

  user = email_objects[0].user
  _send_verification_email(user, email)
  return True


def _send_verification_email(user, email=None):
  if not email:
    email = user.email

  email_verification_url = verification_url_for_user_email(user, email)
  emails.send_verification_email(user, email, email_verification_url)


def email_token_for_reset_token(reset_token):
  try:
    return EmailToken.objects.get(
        token=reset_token,
        kind=EmailToken.KIND_RESET_PASSWORD,
        redemption_time__isnull=True)
  except EmailToken.DoesNotExist:
    return None


def user_for_email_reset_token(reset_token):
  email_token = email_token_for_reset_token(reset_token)
  if email_token:
    return get_user_by_email(email_token.email)
  return None


def reset_password_with_email_token(reset_token, new_password):
  email_token = email_token_for_reset_token(reset_token)
  if not email_token:
    return False

  user = get_user_by_email(email_token.email, for_update=True)
  if not user:
    return False

  email_token.redemption_time = datetime.now()
  email_token.save()

  user.set_password(new_password)
  user.save()

  # Also go ahead and verify this user with this call.
  if user.flags.has_unverified_email:
    verify_email_from_user_token(user, email_token)

  emails.send_reset_password_succeeded_email(user)

  return True
