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
var urls = skit.platform.urls;
var util = skit.platform.util;

var FloatingBox = library.controllers.FloatingBox;
var LKAPIClient = library.api.LKAPIClient;
var ButtonOverlay = library.overlays.ButtonOverlay;

var html = __module__.html;


module.exports = Controller.create(FloatingBox, {
  enableLoggedOut: true,

  __preload__: function(loaded) {
    if (this.user) {
      navigation.navigate(this.redirectUrl());
    }
    loaded();
  },

  __body__: function() {
    var email = navigation.query()['email'];
    var signupUrl = urls.appendParams('/signup/', {'redirect': this.redirectUrl()});
    return html({
      signupUrl: signupUrl,
      email: email
    });
  },

  __ready__: function() {
    var form = dom.get('form');
    this.bind(form, 'submit', this.onSubmitLoginForm, this);
  },

  onSubmitLoginForm: function(evt) {
    evt.preventDefault();

    var form = evt.target;
    var email = form.get('input[name=email]');
    var password = form.get('input[name=password]');
    var button = form.get('button[type=submit]');

    var emailValue = email.value();
    var passwordValue = password.value();

    email.disable();
    password.disable();
    button.disable();

    LKAPIClient.login(emailValue, passwordValue, {
      onSuccess: function() {
        navigation.navigate(this.redirectUrl());
      },
      onError: function(code, response) {
        var message = 'Could not find user';
        var wrongPassword = false;
        if (response && response['error_field'] == 'password') {
          message = 'Incorrect password';
          wrongPassword = true;
        }
        var overlay = new ButtonOverlay(message, 'Please try again.');
        overlay.addDidDismissListener(function() {
          var el = wrongPassword ? password.element : email.element;
          el.focus();
          el.select();
        });
        overlay.addButton('Okay');
        overlay.show();

        email.enable();
        password.enable();
        button.enable();
      },
      context: this
    })
  }
});
