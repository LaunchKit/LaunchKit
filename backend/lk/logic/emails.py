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

import json
import logging
from smtplib import SMTPDataError

from django import template
from django.conf import settings
from django.core import mail
from premailer import Premailer

from backend import celery_app
from backend.util import html_to_text


class LKEmail(object):
  def __init__(self, template_name, subject, to_address,
      template_variables=None,
      from_name=None,
      from_address='noreply@%s' % settings.EMAIL_FROM_DOMAIN,
      reply_to_address=None):

    if from_name is None:
      from_name = 'Help'

    self.template_name = template_name
    self.subject = subject

    self.template_variables = template_variables or {}

    self.to_address = to_address
    self.from_name = from_name
    self.from_address = from_address
    self.reply_to_address = reply_to_address

    self._metadata = {}

  @property
  def _context(self):
    return template.Context(self.template_variables)

  def render_html(self):
    htmly = template.loader.get_template('emails/%s' % self.template_name)
    html = htmly.render(self._context)
    premailer = Premailer(html, remove_classes=False, strip_important=False)
    html = premailer.transform(pretty_print=False)
    return html

  def add_sendgrid_category(self, value):
    if 'category' not in self._metadata:
      self._metadata['category'] = []
    self._metadata['category'].append(value)

  def add_sendgrid_custom_field(self, key, value):
    if 'unique_args' not in self._metadata:
      self._metadata['unique_args'] = {}
    self._metadata['unique_args'][key] = value

  def to_multipart_email(self):
    html_content = self.render_html()
    text_content = html_to_text.plaintextify(html_content)

    headers = {}
    if self._metadata:
      headers['X-SMTPAPI'] = json.dumps(self._metadata)
    if self.reply_to_address:
      headers['Reply-To'] = self.reply_to_address

    email_message = mail.EmailMultiAlternatives(
        self.subject,
        text_content,
        '%s <%s>' % (self.from_name, self.from_address),
        [self.to_address],
        [],
        headers=headers)
    email_message.attach_alternative(html_content, 'text/html')

    return email_message


def send_all(email_objects):
  if not email_objects:
    return

  email_messages = []

  for email in email_objects:
    if not email.to_address:
      logging.warn('Not sending email to %s: %s', email.to_address, email.subject)
      continue
    logging.debug('Sending "%s" to: %s', email.subject, email.to_address)
    message = email.to_multipart_email()
    email_messages.append(message)

  # TODO(Taylor): Render these in the worker.
  _really_send_emails.delay(email_messages)


@celery_app.task(ignore_result=True, queue='email')
def _really_send_emails(email_messages):
  connection = mail.get_connection()

  try:
    connection.send_messages(email_messages)
  except SMTPDataError as e:
    for message in email_messages:
      logging.warn('[%s] Could not send email from: %s with subject: "%s"', e, message.from_email, message.subject)


def create_verification_email(user, email_address, email_verification_url):
  subject = 'Verify E-mail Address'
  template_variables = {
    'user': user,
    'email_address': email_address,
    'email_verification_url': email_verification_url,
  }

  email = LKEmail('verify_email.html',
      subject, email_address,
      template_variables=template_variables)
  email.add_sendgrid_category('verify-email')
  return email


def create_bundle_ready_email(user, screenshot_set, download_url):
  subject = 'Your screenshots are ready!'
  template_variables = {
    'user': user,
    'app_name': screenshot_set.name,
    'app_version': screenshot_set.version,
    'download_url': download_url,
    'public_url': screenshot_set.public_url,
    'twitter_share_url': screenshot_set.twitter_share_url,
  }

  email = LKEmail('screenshots_are_ready.html',
      subject, user.email,
      template_variables=template_variables)
  email.add_sendgrid_category('screenshots-ready')
  return email


def send_bundle_ready_email(user, bundle, download_url):
  message = create_bundle_ready_email(user, bundle, download_url)
  send_all([message])


def send_verification_email(user, email_address, email_verification_url):
  email = create_verification_email(user, email_address, email_verification_url)
  send_all([email])


def create_reset_password_email(user, reset_password_url):
  subject = 'Set New Password'
  template_variables = {
    'user': user,
    'reset_password_url': reset_password_url,
  }

  email = LKEmail('reset_password.html',
      subject, user.email,
      template_variables=template_variables)
  email.add_sendgrid_category('reset-password')

  return email


def send_reset_password_email(user, reset_password_url):
  email = create_reset_password_email(user, reset_password_url)
  send_all([email])


def create_reset_password_succeeded_email(user):
  subject = 'Set New Password Succeeded'
  template_variables = {
    'user': user,
  }

  email = LKEmail('reset_password_succeeded.html',
      subject, user.email,
      template_variables=template_variables)
  email.add_sendgrid_category('reset-password-succeeded')

  return email


def send_reset_password_succeeded_email(user):
  email = create_reset_password_succeeded_email(user)
  send_all([email])


def create_welcome_email(user, verify_url, unsubscribe_url):
  subject = "Welcome!"

  template_variables = {
    'recipient': user,
    'verify_url': verify_url,
    'unsubscribe_url': unsubscribe_url,
  }

  email = LKEmail('welcome.html',
      subject, user.email,
      template_variables=template_variables)
  email.add_sendgrid_category('welcome')

  return email


def create_reviews_ready_email(user, apps):
  if len(apps) == 1:
    subject = 'Reviews for %s are ready!' % apps[0].short_name
  else:
    subject = 'Reviews for your apps are ready!'

  template_variables = {
    'apps': apps,
    'user': user,
    'app_names': [a.short_name for a in apps],
  }

  email = LKEmail('reviews_ready.html',
      subject, user.email,
      from_name='Review Monitor',
      template_variables=template_variables)
  email.add_sendgrid_category('reviews-ingested')

  return email


def create_reviews_subscription_email(created_user, email, apps, unsubscribe_url):
  if len(apps) == 1:
    subject = 'App Store reviews for %s coming to your inbox soon!' % apps[0].short_name
  else:
    subject = 'App Store reviews coming to your inbox soon!'

  template_variables = {
    'created_user': created_user,
    'apps': apps,
    'app_names': [a.short_name for a in apps],
    'unsubscribe_url': unsubscribe_url,
  }

  message = LKEmail('reviews_new_subscription.html',
      subject, email,
      from_name='Review Monitor',
      template_variables=template_variables)
  message.add_sendgrid_category('reviews-new-sub')

  return message


def create_review_email(email, app_info, reviews_count, reviews, unsubscribe_url, created_user=None):
  if reviews_count == 1:
    subject = "%s has a new review!" % app_info.short_name
  else:
    subject = "%s has %s new reviews!" % (app_info.short_name, reviews_count)

  template_variables = {
    'created_user': created_user,
    'reviews': reviews,
    'reviews_count': reviews_count,
    'app': app_info,
    'unsubscribe_url': unsubscribe_url,
  }

  message = LKEmail('reviews_reviews_found.html',
      subject, email,
      from_name='Review Monitor',
      template_variables=template_variables)
  message.add_sendgrid_category('review-new')

  return message


def create_sales_report_email(user, email, app_metrics, total_metrics, requested_date, unsubscribe_url, created_user=None):
  formatted_date = requested_date.strftime('%B %d, %Y')
  subject = 'Daily App Store Analytics for %s' % formatted_date

  template_variables = {
    'app_metrics': app_metrics,
    'total_metrics': total_metrics,
    'formatted_date': formatted_date,
    'unsubscribe_url': unsubscribe_url,
    'created_user': created_user,
  }

  message = LKEmail('sales_report.html',
      subject, email,
      from_name='Sales Reporter',
      template_variables=template_variables)
  message.add_sendgrid_category('sales-report')

  return message
