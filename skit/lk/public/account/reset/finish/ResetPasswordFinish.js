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

var LKAPIClient = library.api.LKAPIClient;
var FloatingBox = library.controllers.FloatingBox;
var ButtonOverlay = library.overlays.ButtonOverlay;

var html = __module__.html;
var doneHtml = __module__.done.html;
var problemHtml = __module__.problem.html;


module.exports = Controller.create(FloatingBox, {
  enableLoggedOut: true,

  __body__: function() {
    var query = navigation.query();
    if (!query['token'] || query['token'].length != 32) {
      return problemHtml();
    }

    return html({email: query['email']});
  },

  __ready__: function() {
    var form = dom.get('#reset-form');
    this.bind(form, 'submit', this.onSubmitForm, this);

    form.get('input[type=password]').element.focus();
  },

  onSubmitForm: function(evt) {
    evt.preventDefault();

    var passwords = evt.target.find('input[type=password]');
    var password = passwords[0];
    var passwordConfirm = passwords[1];

    var passwordValue = password.value();
    if (passwordValue.length < 6) {
      var overlay = new ButtonOverlay('Please provide a password',
          'Passwords should be at least 6 characters long.');
      overlay.addButton('Okay');
      overlay.addDidDismissListener(function() {
        password.element.select();
      });
      overlay.show();
      return;
    }

    if (passwordValue != passwordConfirm.value()) {
      var overlay = new ButtonOverlay('Passwords do not match.');
      overlay.addButton('Okay');
      overlay.addDidDismissListener(function() {
        passwordConfirm.element.select();
      });
      overlay.show();
      return;
    }

    var toDisable = evt.target.find('input, button');
    iter.forEach(toDisable, function($e) {
      $e.disable();
    });

    var token = navigation.query()['token'];
    LKAPIClient.setNewPassword(token, passwordValue, {
      onSuccess: function() {
        var email = navigation.query()['email'] || '';
        var loginUrl = urls.appendParams('/login/', {email: email})
        dom.get('.content').element.innerHTML = doneHtml({
          loginUrl: loginUrl
        });
      },
      onError: function() {
        iter.forEach(toDisable, function($e) {
          $e.enable();
        });

        var okay = new ButtonOverlay('Oops!', 'We could not set that password for some reason.');
        okay.addButton('Okay');
        okay.show();
      },
      context: this
    });
  }
});
