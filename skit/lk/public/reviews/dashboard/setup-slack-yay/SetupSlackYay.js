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

var ButtonOverlay = library.overlays.ButtonOverlay;
var Dashboard = library.controllers.Dashboard;
var LKAPIClient = library.api.LKAPIClient;
var scripts = library.misc.scripts;

var html = __module__.html;


var NEXT_URL = '/reviews/dashboard/setup-twitter/';


module.exports = Controller.create(Dashboard, {
  __preload__: function(done) {
    LKAPIClient.reviewsApps({
      onSuccess: function(apps) {
        this.apps = apps;
      },
      onComplete: function() {
        done();
      },
      context: this
    });
  },

  __body__: function() {
    var app = this.apps && this.apps[0];
    var appName, appIcon;
    if (!app) {
      appName = 'Your App';
      appIcon = '/__static__/images/icon_app_store.png';
    } else {
      appName = app.names.short;
      appIcon = app.icon.small;
    }

    var query = navigation.query();
    var channelName = query['channel'] || null;

    return {
      content: html({
        appName: appName,
        appIcon: appIcon,
        channelName: channelName,
        nextUrl: NEXT_URL
      })
    };
  }
});
