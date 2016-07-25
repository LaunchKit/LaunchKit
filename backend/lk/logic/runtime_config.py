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

from django.db import connection
from django.db import transaction
from django.db.models import Q

from backend.lk.models import MatchOperator
from backend.lk.models import RuntimeConfigRule
from backend.lk.models import RuntimeConfigRuleNamespace
from backend.util import text


SYSTEM_NAMESPACE = 'system'
LIVE_NAMESPACE = 'live'

ALL_RULE_QUALIFIERS = {
  'namespace',
  'build',
  'build_match',
  'version',
  'version_match',
  'bundle_id',
  'ios_version',
  'ios_version_match',
  'debug',
  'sdk_user_labels',
}
ALLOWED_FIND_RULES_ARGS = ALL_RULE_QUALIFIERS | set(['key'])
ALLOWED_UPDATE_RULE_ARGS = ALL_RULE_QUALIFIERS | set(['value', 'description'])


def find_rule(rules, **qualifiers):
  leftovers = set(qualifiers.keys()) - ALL_RULE_QUALIFIERS
  if leftovers:
    raise ValueError('Invalid qualifiers: %s' % leftovers)

  for rule in rules:
    nomatch = False
    for q in ALL_RULE_QUALIFIERS:
      mine = qualifiers.get(q)
      qrule = getattr(rule, q)
      if mine != qrule:
        nomatch = True
        break

    if nomatch:
      continue

    return rule
  return None


def interpret_rules(rules, version=None, build=None, ios_version=None, sdk_user_labels=None, debug=False):
  rules = sorted(rules, key=lambda r: (r.specificity, r.sort_time), reverse=True)

  # DEBUG PRINTING
  # for i, r in enumerate(rules):
  #   print i, r.specificity, r.key, r.bundle_id, r.build, r.build_match, r.version, r.version_match

  for rule in rules:
    if rule.version:
      if not version:
        continue

      version_cmp = text.cmp_version(rule.version, version)
      if rule.version_match == MatchOperator.GREATER_OR_EQUAL:
        if version_cmp > 0:
          continue
      elif rule.version_match == MatchOperator.GREATER:
        if version_cmp >= 0:
          continue
      elif rule.version_match == MatchOperator.EQUAL:
        if version_cmp != 0:
          continue
      elif rule.version_match == MatchOperator.LESS_OR_EQUAL:
        if version_cmp < 0:
          continue
      elif rule.version_match == MatchOperator.LESS:
        if version_cmp <= 0:
          continue

    if rule.build:
      if not build:
        continue

      build_cmp = text.cmp_version(rule.build, build)
      if rule.build_match == MatchOperator.GREATER_OR_EQUAL:
        if build_cmp > 0:
          continue
      elif rule.build_match == MatchOperator.GREATER:
        if build_cmp >= 0:
          continue
      elif rule.build_match == MatchOperator.EQUAL:
        if build_cmp != 0:
          continue
      elif rule.build_match == MatchOperator.LESS_OR_EQUAL:
        if build_cmp < 0:
          continue
      elif rule.build_match == MatchOperator.LESS:
        if build_cmp <= 0:
          continue

    if rule.ios_version:
      if not ios_version:
        continue

      ios_version_cmp = text.cmp_version(rule.ios_version, ios_version)
      if rule.ios_version_match == MatchOperator.GREATER_OR_EQUAL:
        if ios_version_cmp > 0:
          continue
      elif rule.ios_version_match == MatchOperator.GREATER:
        if ios_version_cmp >= 0:
          continue
      elif rule.ios_version_match == MatchOperator.EQUAL:
        if ios_version_cmp != 0:
          continue
      elif rule.ios_version_match == MatchOperator.LESS_OR_EQUAL:
        if ios_version_cmp < 0:
          continue
      elif rule.ios_version_match == MatchOperator.LESS:
        if ios_version_cmp <= 0:
          continue

    # None here means not set at all -- important since this one is a boolean.
    if rule.debug is not None:
      if rule.debug != debug:
        continue

    if rule.sdk_user_labels:
      if not sdk_user_labels:
        continue

      labels = rule.sdk_user_labels.split(',')
      if not all(label in sdk_user_labels for label in labels):
        continue

    return rule.typed_value
  return None


class ConfigInterpreter(object):
  def __init__(self, key, rules=None):
    self.key = key
    self.rules = []
    for r in (rules or []):
      self.add_rule(r)

  def add_rule(self, rule):
    if self.key != rule.key:
      raise ValueError('Provide only rules for a single key')
    self.rules.append(rule)

  def value(self, **kwargs):
    return interpret_rules(self.rules, **kwargs)


def interpolated_config_for_user(user, namespace, bundle_id, **kwargs):
  all_rules = rules_for_user(user, bundle_id, namespace=namespace)

  interpreters = {}
  for rule in all_rules:
    if rule.key not in interpreters:
      interpreters[rule.key] = ConfigInterpreter(rule.key)
    interpreters[rule.key].add_rule(rule)

  values = {}
  for interpreter in interpreters.values():
    value = interpreter.value(**kwargs)
    if value is not None:
      values[interpreter.key] = value
  return values


def interpolated_config_for_session(session):
  return interpolated_config_for_user(
      session.user,
      [LIVE_NAMESPACE, SYSTEM_NAMESPACE],
      session.app.bundle_id,
      version=session.app_version,
      build=session.app_build,
      ios_version=session.os_version,
      debug=session.app_build_debug,
      sdk_user_labels=session.sdk_user.labels)


def rules_for_user(user, bundle_id, limit=None, namespace=None, **kwargs):
  leftovers = set(kwargs.keys()) - ALLOWED_FIND_RULES_ARGS
  if leftovers:
    raise ValueError('Invalid qualifiers: %s' % leftovers)

  if isinstance(namespace, (tuple, list)):
    namespaces_qs = Q()
    for ns in namespace:
      namespaces_qs |= Q(namespace=ns)
  else:
    namespaces_qs = Q(namespace=namespace)

  rules_qs = RuntimeConfigRule.objects.filter(namespaces_qs).filter(user=user, bundle_id=bundle_id).order_by('create_time')

  # Manually filter kwargs here because not all are in fields.
  return list(rule for rule in rules_qs[:limit or 500]
              if all(getattr(rule, k) == kwargs[k] for k in kwargs))


def rules_for_user_key(user, key, bundle_id, **kwargs):
  return rules_for_user(user, bundle_id, key=key, **kwargs)


def _clean_match_args(kwargs):
  if not kwargs.get('version_match') and kwargs.get('version'):
    kwargs['version_match'] = MatchOperator.EQUAL
  if not kwargs.get('build_match') and kwargs.get('build'):
    kwargs['build_match'] = MatchOperator.EQUAL
  if not kwargs.get('ios_version_match') and kwargs.get('ios_version'):
    kwargs['ios_version_match'] = MatchOperator.EQUAL


def create_rule(user, key, kind, value, description=None, **kwargs):
  leftovers = set(kwargs.keys()) - ALL_RULE_QUALIFIERS
  if leftovers:
    raise ValueError('Invalid qualifiers: %s' % leftovers)

  # Set everything not passed here to null.
  for k in ALL_RULE_QUALIFIERS:
    if k not in kwargs:
      kwargs[k] = None

  _clean_match_args(kwargs)

  rule = RuntimeConfigRule(user=user, key=key, kind=kind, description=description)
  for k in kwargs:
    setattr(rule, k, kwargs[k])
  rule.set_typed_value(value)
  rule.save()

  update_namespace_status(user, rule.bundle_id, rule.namespace)

  return rule


def update_rule(rule, value=None, **kwargs):
  leftovers = set(kwargs.keys()) - ALLOWED_UPDATE_RULE_ARGS
  if leftovers:
    raise ValueError('Invalid update options: %s' % leftovers)

  if value is not None:
    rule.set_typed_value(value)

  _clean_match_args(kwargs)

  for k in kwargs:
    setattr(rule, k, kwargs[k])

  rule.save()

  update_namespace_status(rule.user, rule.bundle_id, rule.namespace)

  return rule


@transaction.atomic
def publish_rules(user, source_bundle_id=None, destination_bundle_id=None, source_namespace=None, destination_namespace=LIVE_NAMESPACE):
  cursor = connection.cursor()

  cursor.execute("""
    DELETE FROM lk_runtimeconfigrule
      WHERE user_id = %s
        AND bundle_id = %s
        AND COALESCE(namespace, '') = COALESCE(%s, '');

    INSERT INTO lk_runtimeconfigrule (
        create_time, sort_time, update_time,
        key, kind, bundle_id,
        value,
        user_id, namespace,
        qualifiers)
    (SELECT
        create_time, sort_time, update_time,
        key, kind, %s,
        value,
        user_id, %s,
        qualifiers
     FROM lk_runtimeconfigrule
       WHERE user_id = %s
         AND bundle_id = %s
         AND COALESCE(namespace, '') = COALESCE(%s, '')
    );
  """, [user.id, destination_bundle_id, destination_namespace,
        destination_bundle_id, destination_namespace,
        user.id, source_bundle_id, source_namespace])

  update_namespace_status(user, destination_bundle_id, destination_namespace)


def update_namespace_status(user, bundle_id, namespace):
  published, created = RuntimeConfigRuleNamespace.objects.get_or_create(
      user=user, bundle_id=bundle_id, namespace=namespace)
  published.save()


def namespace_update_time(user, bundle_id, namespace):
  status = RuntimeConfigRuleNamespace.objects.filter(
      user=user, bundle_id=bundle_id, namespace=namespace).first()
  if status:
    return status.update_time
  return None


def rules_published_times_by_bundle_id(user):
  namespace_or = Q(namespace__isnull=True) | Q(namespace=LIVE_NAMESPACE)
  statuses = RuntimeConfigRuleNamespace.objects.filter(namespace_or, user=user)

  statuses_by_bundle = {}
  for status in statuses:
    if status.bundle_id not in statuses_by_bundle:
      statuses_by_bundle[status.bundle_id] = {}
    statuses_by_bundle[status.bundle_id][status.namespace or 'draft'] = status.update_time

  return statuses_by_bundle


def rules_published_status_for_bundle_id(user, bundle_id):
  namespace_or = Q(namespace__isnull=True) | Q(namespace=LIVE_NAMESPACE)
  namespaces = list(
    RuntimeConfigRuleNamespace.objects
      .filter(namespace_or, user=user, bundle_id=bundle_id)
  )

  return {n.namespace or 'draft': n.update_time for n in namespaces}
