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
var navigation = skit.platform.navigation;
var Controller = skit.platform.Controller;

var AmbiguousProgressOverlay = library.overlays.AmbiguousProgressOverlay;
var ButtonOverlay = library.overlays.ButtonOverlay;
var Dashboard = library.controllers.Dashboard;
var LKAPIClient = library.api.LKAPIClient;

var html = __module__.html;


var NEXT_URL = '/sales/onboard/choose-vendor/';


module.exports = Controller.create(Dashboard, {
  __preload__: function(done) {
    LKAPIClient.itunesVendors({
      onSuccess: function(appleId, vendors) {
        if (appleId) {
          // Prevent double-onboarding.
          navigation.navigate('/sales/dashboard/');
        }
      },
      onComplete: done,
      context: this
    });

    done();
  },

  __title__: function() {
    return 'Connect iTunes Connect to ' + this.product.name;
  },

  __body__: function(childHtml) {
    return {
      content: childHtml || html({
        product: this.product
      })
    }
  },

  handleAction: function(type, $target) {
    Dashboard.prototype.handleAction.apply(this, arguments);

    switch (type) {
      case 'connect':
        if (this.connecting) {
          return;
        }
        this.connecting = true;

        var progress = new AmbiguousProgressOverlay('Connecting to iTunes Connect...');
        progress.show();

        var appleId = dom.get('#itunes-apple-id').value();
        var password = dom.get('#itunes-password').value();

        LKAPIClient.itunesConnect(appleId, password, {
          onSuccess: function() {
            navigation.navigate(NEXT_URL);
          },
          onError: function(code, data) {
            progress.done();

            var title = 'Whoops!';
            var message = 'An unknown error occurred. Please try again in a moment.';

            var kind = data && data['errors'] && data['errors']['kind'];
            var error = data && data['errors'] && data['errors']['__all__'];

            if (kind == 'auth') {
              title = 'Authentication Problem';
              message = [
                'Please check your iTunes Connect login credentials and try again.',
                'Note: Two-factor auth is not supported yet.'
              ];

            } else if (kind == 'vendors') {
              title = 'Reporting Access';
              message = [
                'Looks like we can\'t access iTunes Connect sales reports with those credentials.',
                'If you just created this account, it may take several hours for the account to gain access to reporting.',
                '(' + (error || 'unknown error') + ')'
              ];

            } else if (kind == 'connection') {
              title = 'iTunes Connection Problem';
              message = [
                'Looks like we can\'t access iTunes Connect right now. Please try again in a moment.',
                '(' + (error || 'unknown error') + ')'
              ];

            }

            var okay = new ButtonOverlay(title, message);
            okay.addButton('Okay');
            okay.show();

            delete this.connecting;
          },
          context: this
        });

        break;
    }
  }
});
