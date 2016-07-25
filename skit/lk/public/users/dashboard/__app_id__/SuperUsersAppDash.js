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

var dom = skit.browser.dom;
var Controller = skit.platform.Controller;
var iter = skit.platform.iter;
var navigation = skit.platform.navigation;
var urls = skit.platform.urls;
var util = skit.platform.util;
var Handlebars = skit.thirdparty.handlebars;

var LKAnalyticsAPIClient = library.api.LKAnalyticsAPIClient;
var Dashboard = library.controllers.Dashboard;
var moment = third_party.moment;

var html = __module__.html;


function msSinceNow(d) {
  var now = +(new Date());
  var then = d * 1000;
  return now - then;
}

function hasAnyData(user) {
  if (msSinceNow(user['firstVisit']) > 1000 * 60 * 60 * 24) {
    return true;
  }

  var stats = user['stats'];
  return stats['visits'] || stats['seconds'] || stats['screens'] || stats['taps'];
}


Handlebars.registerHelper('ifHasAnyData', function(u, opts) {
  if (hasAnyData(u)) {
    return opts.fn(this);
  } else {
    return opts.inverse(this);
  }
});

Handlebars.registerHelper('sortUrl', function(sortKey) {
  var query = navigation.query();
  if (query['sort_key'] == sortKey) {
    query['sort_key'] = '';
  } else {
    query['sort_key'] = sortKey;
  }

  delete query['start_sdk_user_id'];
  return urls.appendParams('?', query);
});

Handlebars.registerHelper('sortClass', function(sortKey) {
  var query = navigation.query();
  if (query['sort_key'] == sortKey) {
    return 'sorted-by';
  }
  return '';
});

Handlebars.registerHelper('ifOnline', function(context, opts) {
  // Within the last two minutes.
  if (msSinceNow(context) < (60 * 2 * 1000)) {
    return opts.fn(this);
  } else {
    return opts.inverse(this);
  }
});

Handlebars.registerHelper('userScore', function(user) {
  var labelSet = {};
  iter.forEach(user.labels || [], function(l) { labelSet[l] = 1; });

  var status = '';
  var label = '';
  var src = null;
  var html = '';

  if ('super' in labelSet) {
    src = '/__static__/images/users/icon.png';
    status = 'super-user';
    label = 'Super';
  } else if ('almost' in labelSet) {
    src = '/__static__/images/users/icon_grey.png';
    status = 'super-user-fringe';
    label = 'Almost Super';
  } else if ('fringe' in labelSet) {
    status = 'almost-super-user';
    label = 'Previously Super';
  } else if ('active' in labelSet) {
    status = 'active-user';
    label = 'Active';
  } else if (!hasAnyData(user)) {
    status = 'inactive-user';
    label = 'Waiting';
  } else {
    status = 'inactive-user';
    label = 'Inactive';
  }

  if (src) {
    html = '<img src="' + src + '" alt="' + label + '" title="' + label + '">';
  }

  return new Handlebars.SafeString(html);
});


module.exports = Controller.create(Dashboard, {
  __preload__: function(done) {
    var left = 2;
    function maybeFinish() {
      left--;
      if (left) {
        return;
      }

      if (!this.app) {
        navigation.notFound();
      }

      done();
    }

    var query = navigation.query();

    this.selectedAppId = this.params['__app_id__'];
    this.query = query['query'] || '';
    this.sortKey = query['sort_key'] || 'last_accessed_time';
    this.startSDKUserId = query['start_sdk_user_id'] || '';

    var params = {
      'app_id': this.selectedAppId,
      'sort_key': this.sortKey,
      'query': this.query,
      'start_sdk_user_id': this.startSDKUserId
    };

    LKAnalyticsAPIClient.users(params, {
      onSuccess: function(users) {
        this.users = users;
      },
      onComplete: maybeFinish,
      context: this
    });

    LKAnalyticsAPIClient.apps(LKAnalyticsAPIClient.Products.SUPER_USERS, {
      onSuccess: function(apps) {
        this.apps = apps;
        this.app = iter.find(this.apps, function(a) {
          return a['id'] == this.selectedAppId;
        }, this);

        if (this.app) {
          this.app.selected = true;
        }
      },
      onComplete: maybeFinish,
      context: this
    });
  },

  __title__: function() {
    return this.product.name;
  },

  __body__: function() {
    var nextUrl = null;
    if (this.users && this.users.length == 100) {
      nextUrl = urls.appendParams(navigation.relativeUrl(), {
        'start_sdk_user_id': this.users[this.users.length - 1]['id']
      });
    }

    var name = this.app['names']['short'] + ' (Debug)';
    var bundleId = this.app['bundleId'] + '.beta';
    var addDebugAppUrl = urls.appendParams('/users/onboard/custom-app/', {'name': name, 'bundle_id': bundleId});

    return html({
      app: this.app,
      apps: this.apps,
      query: this.query,
      counts: this.app['stats'],
      users: this.users,

      nextUrl: nextUrl,
      addDebugAppUrl: addDebugAppUrl
    });
  },

  handleAction: function(name, $target) {
    Dashboard.prototype.handleAction.apply(this, arguments);

    switch (name) {
      default:
        break;
    }
  }
});
