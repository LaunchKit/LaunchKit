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
      navigation.navigate(this.redirectUrl('/dashboard/'));
    }
    loaded();
  },

  __body__: function() {
    var loginUrl = urls.appendParams('/login/', {'redirect': this.redirectUrl('/dashboard/')});
    return html({
      loginUrl: loginUrl
    });
  },

  __ready__: function() {
    var form = dom.get('form');
    this.bind(form, 'submit', this.onSubmitSignupForm, this);
  },

  onSubmitSignupForm: function(evt) {
    evt.preventDefault();

    var form = evt.target;
    var name = form.get('input[name=name]');
    var email = form.get('input[name=email]');
    var password = form.get('input[name=password]');
    var passwordConfirm = form.get('input[name=password_confirm]');

    var names = name.value().split(/\s+/);
    var firstName = names[0];
    var lastName = names.slice(1).join(' ');
    if (!lastName) {
      var overlay = new ButtonOverlay('Please provide a first and last name.');
      overlay.addButton('Okay');
      overlay.addDidDismissListener(function() {
        name.element.select();
      });
      overlay.show();
      return;
    }

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

    // Snag this before we disable the field.
    var emailValue = email.value();

    name.disable();
    email.disable();
    password.disable();
    passwordConfirm.disable();

    var button = form.get('button');
    button.disable();

    LKAPIClient.signup(firstName, lastName, emailValue, passwordValue, {
      onSuccess: function() {
        // Now log them in.
        LKAPIClient.login(emailValue, passwordValue, {
          onSuccess: function() {
            navigation.navigate(this.redirectUrl('/dashboard/'));
          },
          onError: function() {
            navigation.navigate('/login/');
          },
          context: this
        });
      },
      onError: function(code, response) {
        var errorMessage = response['message'] || 'Please try again in a moment.';
        for (var k in response['errors']) {
          errorMessage = response['errors'][k];
          break;
        }

        var overlay = new ButtonOverlay('Yikes! There was an error.', errorMessage);
        overlay.addButton('Okay');
        overlay.show();

        name.enable();
        email.enable();
        password.enable();
        passwordConfirm.enable();
        button.enable();
      },
      context: this
    })
  }
});
