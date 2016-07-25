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
var object = skit.platform.object;
var urls = skit.platform.urls;

var LKAPIClient = library.api.LKAPIClient;
var App = library.controllers.App;


var STATE_MISMATCH = 'state_mismatch';
var NO_CODE = 'no_code';
var NO_SERVICE = 'no_service';
var INVALID_CODE = 'invalid_code';


module.exports = Controller.create(App, {
  __preload__: function(_loaded) {
    var query = navigation.query();

    var done = function(error) {
      var params = object.copy(query);
      // Remove the slack "code" and "state" from the URL so it can't be copy-pasted.
      delete params['code'];
      delete params['state'];
      if (error) {
        params['error'] = error;
      }

      var doneUrl = urls.appendParams('/account/slack/', params);
      navigation.navigate(doneUrl);
      _loaded();
    }

    if (query['error']) {
      done(query['error']);
      return;
    }

    if (!query['code']) {
      done(NO_CODE);
      return;
    }

    var expectedState = this.user['createTime'];
    if (query['state'] != expectedState) {
      done(STATE_MISMATCH);
      return;
    }

    LKAPIClient.slackTokenFromCode(query['code'], query['service'], query['onboarding'], {
      onSuccess: function(token) {
        done();
      },
      onError: function() {
        done(INVALID_CODE);
      },
      context: this
    });
  }
});

