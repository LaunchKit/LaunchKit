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

var LKAPIClient = library.api.LKAPIClient;
var FloatingBox = library.controllers.FloatingBox;

var html = __module__.html;
var confirmHtml = __module__.confirm.html;


module.exports = Controller.create(FloatingBox, {
  enableLoggedOut: true,

  __body__: function(childHtml) {
    return html();
  },

  __ready__: function() {
    var button = dom.get('#unsubscribe');
    this.bind(button, 'click', this.onClickUnsubscribe, this);
  },

  onClickUnsubscribe: function(evt) {
    evt.preventDefault();

    evt.target.disable();

    var done = function() {
      var container = dom.get('#confirm-container');
      if (!container) {
        return;
      }

      container.element.innerHTML = confirmHtml();
    };

    var token = navigation.query()['token'];
    if (!token) {
      done();
      return;
    }

    LKAPIClient.removeSubscriptionWithToken(token, {
      onComplete: done,
      context: this
    });
  }
});
