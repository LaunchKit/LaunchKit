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
var FloatingBox = library.controllers.FloatingBox;
var ButtonOverlay = library.overlays.ButtonOverlay;

var html = __module__.html;
var checkEmailHtml = __module__.check_email.html;


module.exports = Controller.create(FloatingBox, {
  enableLoggedOut: true,

  __body__: function() {
    return html({user: this.user});
  },

  __ready__: function() {
    var form = dom.get('#reset-form');
    this.bind(form, 'submit', this.onSubmitForm, this);

    form.get('input[type=email]').element.focus();
  },

  onSubmitForm: function(evt) {
    evt.preventDefault();

    var email = evt.target.get('input[type=email]').value();
    var toDisable = evt.target.find('input, button');
    iter.forEach(toDisable, function($e) {
      $e.disable();
    });

    LKAPIClient.resetPassword(email, {
      onSuccess: function() {
        dom.get('.content').element.innerHTML = checkEmailHtml();
      },
      onError: function() {
        iter.forEach(toDisable, function($e) {
          $e.enable();
        });

        var okay = new ButtonOverlay('Oops!', 'We could not find an account with that email address.');
        okay.addButton('Okay');
        okay.show();
      },
      context: this
    });
  }
});
