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


var NEXT_URL = '/reviews/dashboard/';


module.exports = Controller.create(Dashboard, {
  __preload__: function(done) {
    var i = 2;
    function maybeFinish() {
      i--;
      if (!i) {
        done();
      }
    }

    LKAPIClient.setHasBeenReviewsOnboarded({
      onComplete: maybeFinish,
      context: this
    });

    LKAPIClient.reviewSubscriptions({
      onSuccess: function(subscriptions) {
        var hasEmailSub = false;
        this.hasMyEmailSub = false;

        iter.forEach(subscriptions, function(sub) {
          if (sub.email) {
            hasEmailSub = true;
          }
          if (sub.myEmail) {
            this.hasMyEmailSub = true;
          }
        }, this);

        if (hasEmailSub && !navigation.query()['force']) {
          navigation.navigate(NEXT_URL);
        }
      },
      onComplete: maybeFinish,
      context: this
    });
  },

  __body__: function() {
    var mySubscribedEmail = this.hasMyEmailSub ? this.user.email : null;

    return {
      content: html({
        mySubscribedEmail: mySubscribedEmail,
        nextUrl: NEXT_URL
      })
    };
  },

  __ready__: function() {
    var form = dom.get('#email-add-form');
    this.bind(form, 'submit', this.onSubmitEmail, this);
  },

  onSubmitEmail: function(evt) {
    evt.preventDefault();

    var inputs = evt.target.up('form').find('input[type=email]');
    var addresses = [];
    iter.forEach(inputs, function($i) {
      var addr = $i.value();
      if (addr) {
        addresses.push(addr);
      }
    });

    if (!addresses.length) {
      navigation.navigate(NEXT_URL);
      return;
    }

    // GO AHEAD AND SUBSCRIBE

    if (this.subscribing) {
      return;
    }
    this.subscribing = true;

    var toDisable = evt.target.get('button, input');
    iter.forEach(toDisable, function($i) {
      $i.disable();
    });

    var i = addresses.length;
    function maybeFinish() {
      i--;
      if (!i) {
        navigation.navigate(NEXT_URL);
      }
    }

    iter.forEach(addresses, function(email) {
      LKAPIClient.subscribeToReviewsWithEmail(email, {
        onComplete: maybeFinish
      });
    });
  }
});