/**
 * @license
 * Copyright 2016 Cluster Labs, Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

var iter = skit.platform.iter;
var util = skit.platform.util;

var LKAPIClientBase = library.api.LKAPIClientBase;


function parseRule(rule) {
  // TODO(Lance): Modify object here to your heart's content.
  return rule;
}


function filtersFromOptions(options) {
  var params = {};

  if (options.bundleId !== undefined) {
    params['bundle_id'] = options.bundleId || '';
  }
  if (options.version !== undefined) {
    params['version'] = options.version || '';
  }
  if (options.versionMatch !== undefined) {
    params['version_match'] = options.versionMatch || '';
  }
  if (options.build !== undefined) {
    params['build'] = options.build || '';
  }
  if (options.buildMatch !== undefined) {
    params['build_match'] = options.buildMatch || '';
  }
  if (options.namespace !== undefined) {
    params['namespace'] = options.namespace || '';
  }
  if (options.iosVersion !== undefined) {
    params['ios_version'] = options.iosVersion || '';
  }
  if (options.iosVersionMatch !== undefined) {
    params['ios_version_match'] = options.iosVersionMatch || '';
  }

  return params;
}


var LKConfigAPIClient = util.createClass(LKAPIClientBase, {
  isValidValue: function(kind, value) {
    if (value === null || value === undefined) {
      return false;
    }

    if (kind == 'bool') {
      return '' + value === 'false' || '' + value === 'true';
    }

    if (kind == 'int') {
      value = +value;
      return !isNaN(value) && value % 1 === 0;
    }

    if (kind == 'float') {
      value = +value;
      return !isNaN(value);
    }

    // any string is OK.
    return true;
  },

  rules: function(options, callbacks) {
    this.send_('config', {
      method: 'GET',
      params: filtersFromOptions(options),
      parse: function(data) {
        return [iter.map(data['rules'], parseRule), data['status']];
      },
      callbacks: callbacks
    });
  },

  createRule: function(options, callbacks) {
    var params = filtersFromOptions(options);
    params['key'] = options.key;
    params['description'] = options.description || '';
    params['kind'] = options.kind;
    params['value'] = options.value;

    this.send_('config', {
      method: 'POST',
      params: params,
      parse: function(data) {
        return [parseRule(data['rule'])];
      },
      callbacks: callbacks
    });
  },

  editRule: function(rule, callbacks) {
    if (!rule.id) {
      throw new Error('Rule has not been saved yet: ' + rule.key);
    }

    var params = filtersFromOptions(rule);
    params['description'] = rule.description || '';
    params['value'] = rule.value;

    this.send_('config/' + rule['id'], {
      method: 'POST',
      params: params,
      parse: function(data) {
        return [parseRule(data['rule'])];
      },
      callbacks: callbacks
    });
  },

  deleteRule: function(rule, callbacks) {
    this.send_('config/' + rule['id'] + '/delete', {
      method: 'POST',
      callbacks: callbacks
    });
  },

  interpolatedConfig: function(options, callbacks) {
    var params = filtersFromOptions(options);
    this.send_('config_interpolated', {
      method: 'GET',
      params: params,
      parse: function(data) {
        return [data['config']];
      },
      callbacks: callbacks
    });
  },

  publishRules: function(bundleId, callbacks) {
    var params = {};
    params['bundle_id'] = bundleId;

    this.send_('config/publish', {
      method: 'POST',
      params: params,
      callbacks: callbacks
    });
  }
});


module.exports = new LKConfigAPIClient();
