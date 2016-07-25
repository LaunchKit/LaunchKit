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
var SETUP_SLACK_URL = '/account/slack/?service=reviews&onboarding=1';
var SLACK_SETUP_YAY = '/reviews/dashboard/setup-slack-yay/';


module.exports = Controller.create(Dashboard, {
  __preload__: function(done) {
    if (navigation.query()['force']) {
      done();
      return;
    }

    LKAPIClient.reviewSubscriptions({
      onSuccess: function(subscriptions) {
        iter.forEach(subscriptions, function(sub, i, stop) {
          if (sub.slackChannel || sub.slackUrl) {
            var params;
            if (sub.slackChannel) {
              params = {channel: sub.slackChannel.name};
            } else {
              params = {webhook: 1};
            }
            var url = urls.appendParams(SLACK_SETUP_YAY, params);
            navigation.navigate(url);
            stop();
          }
        });
      },
      onComplete: done,
      context: this
    });
  },

  __body__: function() {
    return {
      content: html({
        nextUrl: NEXT_URL,
        setupSlackUrl: SETUP_SLACK_URL
      })
    };
  }
});
