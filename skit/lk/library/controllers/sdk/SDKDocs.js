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

var Controller = skit.platform.Controller;
var cookies = skit.platform.cookies;
var iter = skit.platform.iter;
var object = skit.platform.object;
var navigation = skit.platform.navigation;
var urls = skit.platform.urls;
var util = skit.platform.util;

var LKAnalyticsAPIClient = library.api.LKAnalyticsAPIClient;
var Dashboard = library.controllers.Dashboard;
var products = library.products.products;

var html = __module__.html;


var NAV = [
  [{
    label: 'Overview',
    url: '/sdk/'
  }, {
    label: 'Installation',
    url: '/sdk/install/'
  }],
  [{
    label: 'Super Users',
    url: '/sdk/super-users/',
    dashboardUrl: '/users/dashboard/'
  }, {
    label: 'Cloud Config',
    url: '/sdk/config/',
    dashboardUrl: '/config/dashboard/'
  }],
  [{
    label: 'Send Instructions',
    url: '/sdk/share/',
    icon: 'fa-envelope',
    requireUser: true
  }]
];


var SDKDocs = Controller.create(Dashboard, {
  enableLoggedOut: true,

  TOKEN_COOKIE_NAME: 'sdk-token',
  BACK_URL_COOKIE_NAME: 'sdk-back-url',

  getCurrentToken: function(done) {
    var tryGettingUserToken = util.bind(function() {
      if (!this.user) {
        done();
        return;
      }

      LKAnalyticsAPIClient.getOrCreateAppToken({
        onSuccess: function(token) {
          this.token = token['token'];
        },
        onComplete: done,
        context: this
      });
    }, this);

    var maybeToken = cookies.get(this.TOKEN_COOKIE_NAME);
    if (maybeToken) {
      LKAnalyticsAPIClient.identifyToken(maybeToken, {
        onSuccess: function(valid, lastUsedTime, owner) {
          if (valid) {
            this.token = maybeToken;
            if (!this.user || this.user.id != owner.id) {
              this.tokenOwner = owner;
            }
            done();

          } else {
            tryGettingUserToken();
          }
        },
        onError: function() {
          tryGettingUserToken();
        },
        context: this
      });

      return;
    }

    tryGettingUserToken();
  },

  __preload__: function(done) {
    var redirectUrl = this.redirectUrl('default');
    if (redirectUrl != 'default') {
      cookies.set(this.BACK_URL_COOKIE_NAME, redirectUrl, {
        expires: new Date(+(new Date()) + 1000 * 60 * 60)
      });

      var path = urls.parse(navigation.url()).path;
      navigation.navigate(path);
      done();
      return;
    }

    this.getCurrentToken(done);
  },

  __load__: function() {
    var selectedItem = null;
    var hasUser = !!this.user;
    var path = urls.parse(navigation.url()).path;
    this.nav = iter.filter(iter.map(NAV, function(arr) {
      arr = iter.map(arr, function(item) {
        item = object.copy(item);
        if (item.requireUser && !hasUser) {
          return null;
        }
        if (item.url == path) {
          item.selected = true;
          selectedItem = item;
        }
        return item;
      });
      return iter.filter(arr, function(item) { return !!item; });
    }), function(arr) { return arr.length > 0; });

    this.selectedItem = selectedItem;
    this.backUrl = cookies.get(this.BACK_URL_COOKIE_NAME)
  },

  __title__: function() {
    if (this.title) {
      return this.title + ' - SDK Documentation';
    }
    return 'SDK';
  },

  __body__: function(contentHtml) {

    return html({
      nav: this.nav,

      selectedItem: this.selectedItem,
      backUrl: this.backUrl,

      user: this.user,
      tokenOwner: this.tokenOwner,

      contentHtml: contentHtml
    });
  }
});


module.exports = SDKDocs;