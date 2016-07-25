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

from django import forms
from django.contrib import auth
from django.conf import settings
from django.core import validators

from backend.lk.logic import destructive
from backend.lk.logic import oauth
from backend.lk.logic import users
from backend.lk.models import User
from backend.lk.views.base import api_response
from backend.lk.views.base import api_view
from backend.lk.views.base import api_user_view
from backend.lk.views.base import bad_request
from backend.lk.views.base import not_found
from backend.lk.views.base import ok_response
from backend.util import lkforms


PHONE_TOKEN_VALIDATOR = validators.RegexValidator(regex=r'^[0-9]{6}$')


class UserSignupForm(forms.Form):
  first_name = lkforms.LKSingleLineCharField(max_length=30)
  last_name = lkforms.LKSingleLineCharField(max_length=30)

  password = lkforms.LKPasswordField(label='Password', widget=forms.PasswordInput)

  email = lkforms.LKEmailField(required=True)

  def clean_email(self):
    email = self.cleaned_data['email']
    if email and not users.email_is_reassignable(email):
      raise forms.ValidationError('A user already exists with that email.')
    return email


@api_view('POST')
def signup(request):
  if request.user.is_authenticated():
    return bad_request('You are already signed in.')

  user_form = UserSignupForm(request.POST)
  if not user_form.is_valid():
    return bad_request(message='Invalid user signup data', errors=user_form.errors)

  email = user_form.cleaned_data.get('email')

  password = user_form.cleaned_data['password']
  user = users.create_user(
      user_form.cleaned_data['first_name'],
      user_form.cleaned_data['last_name'],
      email=email,
      password=password)

  if not user:
    logging.warn('Unaccounted for signup error with signup data: %r', user_form.cleaned_data)
    return bad_request('Could not create a user with the given credentials.')

  return api_response({
    'user': user.to_dict(),
  })


#
# OAUTH
#


class OAuthTokenForm(forms.Form):
  client_id = forms.ChoiceField(choices=settings.OAUTH_CLIENT_CHOICES)
  client_secret = forms.CharField(max_length=256)

  def clean_client_secret(self):
    client_secret = self.cleaned_data['client_secret']
    client_id = self.cleaned_data.get('client_id')
    client = settings.OAUTH_CLIENTS_BY_ID.get(client_id)
    if not client:
      return None

    if client.secret != client_secret:
      raise forms.ValidationError('Invalid secret for this client ID.')

    return client_secret


class OAuthGrantTokenForm(OAuthTokenForm):
  scope = forms.ChoiceField(choices=settings.OAUTH_SCOPE_CHOICES)
  grant_type = forms.ChoiceField(choices=settings.OAUTH_GRANT_CHOICES)


@api_view('GET')
def oauth2_auth_view(request):
  return api_response({'message': 'Not yet supported.'}, status=501)


def _oauth_error_response(error_code, state, error_description=None, error_field=None):
  response_dict = {'error': error_code}
  if state:
    response_dict['state'] = state
  if error_description:
    response_dict['error_description'] = error_description
  if error_field:
    response_dict['error_field'] = error_field
  return api_response(response_dict, status=400)


@api_view('POST')
def oauth2_token_view(request):
  form = OAuthGrantTokenForm(request.POST)
  state = request.POST.get('state')

  if not form.is_valid():
    # Errors from: http://tools.ietf.org/html/rfc6749#section-5.2
    # TODO(taylor): When adding support for third-party clients, add
    # "unauthorized_client" support -- this should fire when third-party
    # clients try using one of the privileged/reserved grant_types.
    error_code = 'invalid_request'
    if 'client_id' in form.errors or 'client_secret' in form.errors:
      error_code = 'invalid_client'
    elif 'grant_type' in form.errors:
      error_code = 'unsupported_grant_type'
    return _oauth_error_response(error_code, state)

  # We'll need this later.
  scope = form.cleaned_data['scope']
  # Depending on grant type, perform authentication.
  grant_type = form.cleaned_data['grant_type']

  if grant_type == settings.OAUTH_GRANT_PASSWORD:
    username = request.POST.get('username', '')
    password = request.POST.get('password', '')
    user_exists = False

    user = None
    email = lkforms.clean_email(username)
    if email:
      maybe_user = users.get_user_by_email(email, for_update=True)
      if maybe_user:
        user_exists = True
        if maybe_user.check_password(password):
          user = maybe_user

    if not user:
      return _oauth_error_response('invalid_grant', state,
          error_description='Could not find the user with that email and password.',
          error_field=user_exists and 'password' or 'username')

  # Create a token for this user.
  client_id = form.cleaned_data['client_id']
  access_token = oauth.create_token_for_user_client_scope(user, client_id, scope)

  response_dict = {
    'access_token': access_token,
    'token_type': 'Bearer',
  }
  if state:
    response_dict['state'] = state
  return api_response(response_dict)


@api_view('POST')
def oauth2_invalidate_token_view(request):
  form = OAuthTokenForm(request.POST)
  state = request.POST.get('state')
  if not form.is_valid():
    error_code = 'invalid_request'
    if 'client_id' in form.errors or 'client_secret' in form.errors:
      error_code = 'invalid_client'
    return _oauth_error_response(error_code, state)

  raw_token = request.POST.get('access_token')
  client_id = form.cleaned_data['client_id']
  invalidated = False
  if raw_token:
    invalidated = oauth.invalidate_client_token(client_id, raw_token)

  if not invalidated:
    return _oauth_error_response('invalid_request', state, 'Could not find that access_token.')

  return ok_response()


#
# ACCOUNT MANAGEMENT
#


class ResetPasswordForm(forms.Form):
  email = lkforms.LKEmailField()


@api_view('POST')
def reset_password_view(request):
  form = ResetPasswordForm(request.POST)
  if not form.is_valid():
    return bad_request('Bad reset password request',
        errors=form.errors)

  success = users.request_reset_password_email(form.cleaned_data['email'])
  if not success:
    return bad_request('Could not find a user with that email address')

  return ok_response()


class SetNewPasswordForm(forms.Form):
  token = forms.CharField(min_length=32, max_length=32)
  password = lkforms.LKPasswordField()


@api_view('POST')
def reset_password_finish_view(request):
  form = SetNewPasswordForm(request.POST)
  if not form.is_valid():
    return bad_request('Bad reset password request', errors=form.errors)

  token = form.cleaned_data['token']
  password = form.cleaned_data['password']

  success = users.reset_password_with_email_token(token, password)
  if not success:
    return bad_request('Invalid token data.')

  return ok_response()


class VerifyEmailForm(forms.Form):
  token = forms.CharField(min_length=32, max_length=32)


def verify_email_view(request):
  form = VerifyEmailForm(request.POST)
  if not form.is_valid():
    return bad_request('Bad verification request', errors=form.errors)

  token = form.cleaned_data['token']

  success = users.verify_email_from_token(token)
  if not success:
    return bad_request('Invalid token data.')

  return ok_response()


class UnsubscribeForm(forms.Form):
  token = forms.CharField(min_length=10, max_length=512)


def unsubscribe_view(request):
  form = UnsubscribeForm(request.POST)
  if not form.is_valid():
    return bad_request('Bad unsub request', errors=form.errors)

  token = form.cleaned_data['token']

  success = users.unsubscribe_with_token(token)
  if not success:
    return bad_request('Invalid token data.')

  return ok_response()


#
# VIEW THIS USER
#


@api_user_view('GET')
def user(request):
  return api_response({'user': request.user.to_dict()})


#
# SETTINGS
#


class UserDetailsEditForm(forms.Form):
  first_name = lkforms.LKSingleLineCharField(max_length=30, required=False)
  def clean_first_name(self):
    first_name = self.cleaned_data.get('first_name')
    if 'first_name' in self.data and not first_name:
      raise forms.ValidationError('First name must not be blank')
    return first_name

  last_name = lkforms.LKSingleLineCharField(max_length=30, required=False)
  def clean_last_name(self):
    last_name = self.cleaned_data.get('last_name')
    if 'last_name' in self.data and not last_name:
      raise forms.ValidationError('Last name must not be blank')
    return last_name


@api_user_view('GET', 'POST')
def user_details(request):
  def _build_response():
    user = User.get_cached(request.user.id)

    flags = {}
    for flag in users.USER_EDITABLE_USER_FLAGS:
      flags[flag] = bool(getattr(user.flags, flag))

    return api_response({
      'user': user.to_dict(),
      'emails': [email.to_dict() for email in user.emails_set.all()],
      'settings': flags
    })

  if request.method != 'POST':
    return _build_response()

  # Get an exclusive lock on this user.
  user = User.objects.select_for_update().get(pk=request.user.id)

  # Edit details.
  flag_updates = {}
  for flag in users.USER_EDITABLE_USER_FLAGS:
    if flag in request.POST:
      flag_value = request.POST[flag]
      if flag_value not in ('1', '0'):
        return bad_request(message='Bad flag value.', errors={flag: 'Provided value should be "1" or "0"'})
      flag_updates[flag] = (flag_value == '1')

  if flag_updates:
    users.update_user_flags(user, flag_updates)

  form = UserDetailsEditForm(request.POST)
  if not form.is_valid():
    return bad_request(message='Invalid edit fields.', errors=form.errors)

  update_fields = []
  if 'first_name' in request.POST:
    user.first_name = form.cleaned_data['first_name']
    update_fields.append('first_name')
  if 'last_name' in request.POST:
    user.last_name = form.cleaned_data['last_name']
    update_fields.append('last_name')

  if update_fields:
    user.save(update_fields=update_fields)

  return _build_response()


@api_view('POST')
def request_verification_email(request):
  email = None
  if 'email' in request.POST or not request.user.is_authenticated():
    # Should this be a separate form? Meh.
    form = ResetPasswordForm(request.POST)
    if not form.is_valid():
      return bad_request('Bad email verification request',
          errors=form.errors)
    email = form.cleaned_data['email']

  if request.user.is_authenticated():
    unverified_emails = users.get_unverified_emails(request.user)
    if not unverified_emails:
      return bad_request('No unverified emails for this account.')

    if not email:
      email = unverified_emails[0]
    elif email not in unverified_emails:
      return bad_request('Could not find this unverified email address.')

  success = users.request_verification_email(email)
  if not success:
    return bad_request('Could not request a verification email. Has the email already been verified?')

  return ok_response()


class EmailForm(forms.Form):
  email = lkforms.LKEmailField()


@api_user_view('POST', 'GET')
def emails_view(request):
  user_emails = list(request.user.emails_set.all())
  if request.method == 'GET':
    return api_response({
      'emails': [email.to_dict() for email in user_emails],
    })

  if len([e for e in user_emails if not e.verified]) > 3:
    return bad_request('Cannot add another unverified email address.',
        errors={'email': ['Too many unverified email addresses.']})

  form = EmailForm(request.POST)
  if not form.is_valid():
    return bad_request('Invalid email address.', errors=form.errors)

  new_email = form.cleaned_data['email']
  if new_email in [e.email for e in user_emails]:
    return bad_request('Cannot add an email you already have.',
        errors={'email': ['Account already associated with that address.']})

  email = users.associate_user_with_email(request.user,
      new_email, verified=False)
  if not email:
    return bad_request('Email is already in use.',
        errors={'email': ['Sorry, that email is already in use.']},
        status=409)

  return api_response({
    'email': email.to_dict(),
  })


@api_user_view('POST')
def email_set_primary_view(request):
  form = EmailForm(request.POST)
  if not form.is_valid():
    return bad_request('Invalid email provided.', errors=form.errors)

  if not users.make_email_primary(request.user, form.cleaned_data['email']):
    return bad_request('Could not promote email address to primary.')

  return api_response({
    'emails': [e.to_dict() for e in request.user.emails_set.all()],
  })


@api_user_view('POST')
def email_delete_view(request):
  form = EmailForm(request.POST)
  if not form.is_valid():
    return bad_request('Invalid email provided.', errors=form.errors)

  if not users.disassociate_user_with_email(request.user, form.cleaned_data['email']):
    return bad_request('Could not disassociate that email address.')

  return api_response({
    'emails': [e.to_dict() for e in request.user.emails_set.all()],
  })


@api_user_view('GET')
def user_by_id(request, user_id=None):
  user = User.find_by_encrypted_id(user_id)
  if not user:
    return not_found()

  return api_response({
    'user': user.to_minimal_dict()
  })



#
# DELETE THIS ACCOUNT
#


@api_user_view('POST')
def delete_account_view(request):
  email = request.POST.get('email')
  if email != request.user.email:
    return bad_request('Please provide the current account email address, `email`.')

  destructive.delete_account(request.user)

  return ok_response()
