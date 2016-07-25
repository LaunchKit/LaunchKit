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

var LKAPIClient = library.api.LKAPIClient;
var ButtonOverlay = library.overlays.ButtonOverlay;
var Dashboard = library.controllers.Dashboard;

var html = __module__.html;


var NEXT_URL = '/sales/dashboard/';


module.exports = Controller.create(Dashboard, {
  __preload__: function(done) {
    LKAPIClient.itunesVendors({
      onSuccess: function(appleId, vendors) {
        var hasAlreadyChosen = iter.find(vendors, function(v) { return v['chosen'] });
        if (hasAlreadyChosen) {
          navigation.navigate(NEXT_URL);
          return;
        }

        this.vendors = vendors;
      },
      onComplete: done,
      context: this
    });
  },

  __title__: function() {
    return 'Choose iTunes Vendor';
  },

  __body__: function() {
    return {
      content: html({
        vendors: this.vendors
      })
    }
  },

  handleAction: function(type, $target) {
    Dashboard.prototype.handleAction.apply(this, arguments);

    switch(type) {
      case 'choose':
        if(this.choosing) {
          return;
        }
        this.choosing = true;

        var vendorId = dom.get('#choose-vendor-form').serializeForm()['vendor-id'];

        LKAPIClient.chooseVendor(vendorId, {
          onSuccess: function() {
            navigation.navigate(NEXT_URL);
          },
          onError: function() {
            var okay = new ButtonOverlay('Whoops!', 'We ran into a problem, please try again.');
            okay.addButton('Okay');
            okay.show();

            delete this.choosing;
          },
          context: this
        });

        break;
    }
  }
});
