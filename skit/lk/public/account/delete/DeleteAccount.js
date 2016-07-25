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
var navigation = skit.platform.navigation;

var FloatingBox = library.controllers.FloatingBox;
var ButtonOverlay = library.overlays.ButtonOverlay;
var LKAPIClient = library.api.LKAPIClient;

var html = __module__.html;


module.exports = Controller.create(FloatingBox, {
  __title__: function() {
    return 'Delete Account';
  },

  __body__: function() {
    return html({user: this.user});
  },

  handleAction: function(action) {
    FloatingBox.prototype.handleAction.apply(this, arguments);
    if (action != 'delete-account') {
      return;
    }

    var $email = dom.get('#delete-email');
    var email = $email.value();
    if (email != this.user.email) {
      var overlay = new ButtonOverlay('Incorrect Email Address', 'Please enter your email address.');
      overlay.addButton('Okay', function() {
        $email.element.focus();
        $email.element.select();
      });
      overlay.show();
      return;
    }

    LKAPIClient.deleteUserAccount(email, {
      onComplete: function() {
        navigation.navigate(navigation.relativeUrl());
      }
    });
  }
});
