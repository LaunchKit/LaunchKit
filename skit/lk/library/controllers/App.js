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
var cookies = skit.platform.cookies;
var navigation = skit.platform.navigation;
var urls = skit.platform.urls;
var util = skit.platform.util;
var Controller = skit.platform.Controller;

var Base = library.controllers.Base;


module.exports = Controller.create(Base, {
  // Overrideable by children.
  enableLoggedOut: false,

  redirectToLogin: function() {
    var loginOrSignup = this.preferSignupNotLogin ? '/signup/' : '/login/';
    var redirectUrl = urls.appendParams(loginOrSignup, {'redirect': navigation.relativeUrl()});
    navigation.navigate(redirectUrl);
  },

  __preload__: function(loaded) {
    if (!this.user && !this.enableLoggedOut && !this.dontLoadUser) {
      this.redirectToLogin();
    }

    loaded();
  }
});
