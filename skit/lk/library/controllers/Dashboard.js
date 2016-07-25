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

var layout = skit.browser.layout;
var cookies = skit.platform.cookies;
var Controller = skit.platform.Controller;
var PubSub = skit.platform.PubSub;
var iter = skit.platform.iter;
var navigation = skit.platform.navigation;

var LKAPIClient = library.api.LKAPIClient;
var App = library.controllers.App;
var scripts = library.misc.scripts;
var AmbiguousProgressOverlay = library.overlays.AmbiguousProgressOverlay;
var ButtonOverlay = library.overlays.ButtonOverlay;
// required for better bundling.
var dashboardintro = library.products.dashboardintro;
var products = library.products.products;

var html = __module__.html;


module.exports = Controller.create(App, {
  showHelpButton: false,
  fullWidthContent: false,

  __load__: function(child) {
    this.isOnboarding = navigation.url().indexOf('/onboard/') > 0;
  },

  __body__: function(child) {
    return html({
      content: (typeof child == 'string' ? child : (child.content || '')),
      sidebar: child.sidebar || '',

      currentProduct: this.product || '',
      isOnboarding: this.isOnboarding,
      fullWidthContent: this.fullWidthContent,
      user: this.user
    });
  },

  __ready__: function() {
    var query = navigation.query();

    var shown = false;
    PubSub.sharedPubSub().subscribe(LKAPIClient.SITE_READONLY_NOTIFICATION, function() {
      if (shown) {
        return;
      }
      shown = true;

      var overlay = new ButtonOverlay('Temporary Downtime',
          ['Sorry, the site is temporarily undergoing maintenance.',
           'This should last no longer than 30 minutes. Please try again in a moment.']);
      overlay.addButton('Okay', function() {
        shown = false;
      });
      overlay.show();
    });
  },

  isOnLastPage: function() {
    var windowHeight = layout.height(window);
    var currentPosition;
    var scrollHeight;
    if (!document.body.scrollTop) {
      currentPosition = windowHeight + document.documentElement.scrollTop;
      scrollHeight = document.documentElement.scrollHeight;
    } else {
      currentPosition = windowHeight + document.body.scrollTop;
      scrollHeight = document.body.scrollHeight;
    }
    return currentPosition > scrollHeight - windowHeight;
  }
});
