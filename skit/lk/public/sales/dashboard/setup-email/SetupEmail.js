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

var html = __module__.html;


var NEXT_URL = '/sales/dashboard/setup-extra-email/';


module.exports = Controller.create(Dashboard, {

  __title__: function() {
    return 'Activate ' + this.product.name + ' Emails';
  },

  __body__: function() {
    return {
      content: html({
        nextUrl: NEXT_URL
      })
    };
  },

  handleAction: function(action, $target) {
    switch(action) {
      case 'subscribe':
        LKAPIClient.subscribeToSalesReportsWithMyEmail({
          onComplete: function() {
            navigation.navigate(NEXT_URL);
          }
        })
        break;
    }
  }
});
