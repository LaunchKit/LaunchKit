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
var string = skit.platform.string;
var urls = skit.platform.urls;
var util = skit.platform.util;
var Handlebars = skit.thirdparty.handlebars;

var Dashboard = library.controllers.Dashboard;
var LKAnalyticsAPIClient = library.api.LKAnalyticsAPIClient;
var SDKDocs = library.controllers.sdk.SDKDocs;

var html = __module__.html;



module.exports = Controller.create(SDKDocs, {
  __body__: function() {
    return html({
      token: this.token
    });
  },

  __ready__: function() {
    this.maybeCheckConfigured();

    // Check as long as we're getting some mousemove or touch events.
    this.bind(window, 'mousemove', function(){
      this.maybeCheckConfigured();
    }, this);
    this.bind(document.body, 'touchupinside', function(){
      this.maybeCheckConfigured();
    }, this);
  },

  maybeCheckConfigured: function() {
    if (this.lastUsedTime || !this.token) {
      return;
    }

    if (this.checkConfiguredTimeout_) {
      return;
    }

    this.checkConfiguredTimeout_ = util.setTimeout(function() {
      delete this.checkConfiguredTimeout_;

      this.checkConfigured();
    }, 2000, this);
  },

  checkConfigured: function() {
    LKAnalyticsAPIClient.identifyToken(this.token, {
      onSuccess: function(_, lastUsedTime) {
        if (lastUsedTime) {
          this.lastUsedTime = lastUsedTime;
          dom.get('#sdk-configured-check').addClass('configured');
        }
      },
      context: this
    });
  }

});
