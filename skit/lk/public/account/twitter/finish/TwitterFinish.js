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

var Controller = skit.platform.Controller;
var navigation = skit.platform.navigation;
var urls = skit.platform.urls;

var LKAPIClient = library.api.LKAPIClient;
var App = library.controllers.App;


module.exports = Controller.create(App, {
  __preload__: function(loaded) {
    var query = navigation.query();
    var redirectUrl = query['redirect_url'];
    var appId = query['app_id'];

    var done = function(error) {
      var doneUrl = '/reviews/dashboard/setup-twitter-accounts/';
      var complete = function() {
        navigation.navigate(doneUrl);
        loaded();
      }

      if (error) {
        doneUrl += '?error=1';
        complete();
      }
      else if (redirectUrl) {
        doneUrl = decodeURIComponent(redirectUrl);
        complete();
      }
      else {
        LKAPIClient.autoSubscribeToReviewsWithTwitter(appId, {
          onComplete: complete,
          context: this
        });
      }
    }

    var error = query['error'];
    var token = query['oauth_token'];
    var verifier = query['oauth_verifier'];
    if (error || !(token && verifier)) {
      done(error);
      return;
    }

    LKAPIClient.twitterConnectFinish(token, verifier, appId, {
      onError: function() {
        done(true);
      },
      onComplete: function() {
        done();
      },
      context: this
    });
  }
});

