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
var object = skit.platform.object;
var util = skit.platform.util;

var LKAPIClientBase = library.api.LKAPIClientBase;


var SuperUsersSessionFrequency = {
  MoreThanOnceADay: 'Mvpd',
  OnceADay: '1vpd',
  FiveDaysAWeek: '5vpw',
  ThreeDaysAWeek: '3vpw',
  OnceAWeek: '1vpw',
  TwiceAMonth: '2vpm'
};
var SuperUsersSessionFrequencyOptions = [
  {value: SuperUsersSessionFrequency.MoreThanOnceADay, label: 'More than once a day' },
  {value: SuperUsersSessionFrequency.OnceADay,         label: 'Daily' },
  {value: SuperUsersSessionFrequency.FiveDaysAWeek,    label: 'Five days a week' },
  {value: SuperUsersSessionFrequency.ThreeDaysAWeek,   label: 'Three days a week' },
  {value: SuperUsersSessionFrequency.OnceAWeek,        label: 'Once a week'}
];
var SuperUserSessionFrequencyLabelByValue = {};
iter.forEach(SuperUsersSessionFrequencyOptions, function(opt) {
  SuperUserSessionFrequencyLabelByValue[opt.value] = opt.label;
});

var SuperUsersTimeUsed = {
  HourPerDay: '1hpd',
  FifteenMinutesPerDay: '15mpd',
  FiveMinutesPerDay: '5mpd',
  OneMinutePerDay: '1mpd',
  ThirtySecondsPerDay: '30spd'
};
var SuperUsersTimeUsedOptions = [
  {value: SuperUsersTimeUsed.HourPerDay,           label: 'One hour per day'},
  {value: SuperUsersTimeUsed.FifteenMinutesPerDay, label: 'Fifteen minutes per day'},
  {value: SuperUsersTimeUsed.FiveMinutesPerDay,    label: 'Five minutes per day'},
  {value: SuperUsersTimeUsed.OneMinutePerDay,      label: 'One minute per day'},
];
var SuperUserTimeUsedLabelByValue = {};
iter.forEach(SuperUsersTimeUsedOptions, function(opt) {
  SuperUserTimeUsedLabelByValue[opt.value] = opt.label;
});


var LKAnalyticsAPIClient = util.createClass(LKAPIClientBase, {
  Products: {
    SUPER_USERS: 'super_users',
    CONFIG: 'config',
    RELEASE_NOTES: 'release_notes',
    ONBOARDING: 'onboarding',
    RATING_PROMPT: 'rating_prompt'
  },

  SuperUsersSessionFrequency: SuperUsersSessionFrequency,
  SuperUsersSessionFrequencyLabels: SuperUserSessionFrequencyLabelByValue,

  SuperUsersTimeUsed: SuperUsersTimeUsed,
  SuperUsersTimeUsedLabels: SuperUserTimeUsedLabelByValue,

  superUsersFrequencyOptions: function(selectedValue) {
    return iter.map(SuperUsersSessionFrequencyOptions, function(option) {
      option = object.copy(option);
      option['selected'] = (option['value'] == selectedValue) ? 'selected' : '';
      return option;
    }, this);
  },
  superUsersTimeUsedOptions: function(selectedValue) {
    return iter.map(SuperUsersTimeUsedOptions, function(option) {
      option = object.copy(option);
      option['selected'] = (option['value'] == selectedValue) ? 'selected' : '';
      return option;
    }, this);
  },

  // SDK TOKENS

  listAppTokens: function(callbacks) {
    this.send_('sdk/tokens', {
      method: 'GET',
      parse: function(data) {
        return [data['tokens']];
      },
      callbacks: callbacks
    });
  },

  createAppToken: function(callbacks) {
    this.send_('sdk/tokens/create', {
      method: 'POST',
      parse: function(data) {
        return [data['token']];
      },
      callbacks: callbacks
    });
  },

  getOrCreateAppToken: function(callbacks) {
    this.send_('sdk/tokens/get_or_create', {
      method: 'POST',
      parse: function(data) {
        return [data['token']];
      },
      callbacks: callbacks
    });
  },

  expireAppToken: function(tokenId, callbacks) {
    this.send_('sdk/tokens/' + tokenId + '/expire', {
      method: 'POST',
      parse: function(data) {
        return [data['token']];
      },
      callbacks: callbacks
    });
  },

  // APPS

  createAppWithOptions: function(options, callbacks) {
    var params = {};

    if (options.name) {
      params['display_name'] = options.name;
    }
    if (options.bundleId) {
      params['bundle_id'] = options.bundleId;
    }
    if (options.iTunesId) {
      params['itunes_id'] = options.iTunesId;
      params['itunes_country'] = options.iTunesCountry;
    }
    if (options.configParentId) {
      params['config_parent_id'] = options.configParentId;
    }

    if (options.product) {
      params[options.product] = '1';
    }

    this.send_('sdk/apps', {
      method: 'POST',
      params: params,
      parse: function(data) {
        var app = data['app'];
        return [app];
      },
      callbacks: callbacks
    });
  },

  editAppDetails: function(appId, options, callbacks) {
    var params = {};

    if (options.name !== undefined) {
      params['display_name'] = options.name;
    }
    if (options.superFreq) {
      params['super_freq'] = options.superFreq;
    }
    if (options.superTime) {
      params['super_time'] = options.superTime;
    }
    if (options.configParentId !== undefined) {
      params['config_parent_id'] = options.configParentId;
    }

    this.send_('sdk/apps/' + appId, {
      method: 'POST',
      params: params,
      parse: function(data) {
        var app = data['app'];
        return [app];
      },
      callbacks: callbacks
    });
  },

  apps: function(productOrOptions, callbacks) {
    var params = {};
    if (productOrOptions.length) {
      params['product'] = productOrOptions;
    } else {
      if (productOrOptions.product) {
        params['product'] = productOrOptions.product;
      }
      if (productOrOptions.onlyConfigParents) {
        params['only_config_parents'] = '1';
      }
    }

    this.send_('sdk/apps', {
      method: 'GET',
      params: params,
      parse: function(data) {
        var apps = data['apps'];
        return [apps];
      },
      callbacks: callbacks
    });
  },
  appWithId: function(appId, callbacks) {
    this.send_('sdk/apps/' + encodeURIComponent(appId), {
      method: 'GET',
      parse: function(data) {
        var app = data['app'];
        return [app];
      },
      callbacks: callbacks
    });
  },
  appStoreInfoForAppId: function(appId, callbacks) {
    this.send_('sdk/apps/' + appId + '/itunes', {
      method: 'GET',
      parse: function(data) {
        var info = data['info'];
        return [info];
      },
      callbacks: callbacks
    });
  },

  users: function(params, callbacks) {
    this.send_('user_intelligence/users', {
      method: 'GET',
      params: params,
      parse: function(data) {
        var users = data['users'];
        return [users];
      },
      callbacks: callbacks
    });
  },

  userDetails: function(userId, callbacks) {
    this.send_('user_intelligence/users/' + userId, {
      method: 'GET',
      parse: function(data) {
        var user = data['user'];
        var clientUser = data['clientUser'];
        var app = data['app'];
        var daysActive = data['daysActive'];
        return [user, clientUser, app, daysActive];
      },
      callbacks: callbacks
    });
  },

  visits: function(params, callbacks) {
    this.send_('user_intelligence/visits', {
      method: 'GET',
      params: params,
      parse: function(data) {
        var visits = data['visits'];
        return [visits];
      },
      callbacks: callbacks
    });
  },

  identifyToken: function(token, callbacks) {
    this.send_('sdk/tokens/identify/' + token, {
      method: 'GET',
      parse: function(data) {
        return [data['valid'], data['lastUsedTime'], data['owner']];
      },
      callbacks: callbacks
    });
  }
});


return new LKAnalyticsAPIClient();