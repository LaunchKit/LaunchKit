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
var Dashboard = library.controllers.Dashboard;

var html = __module__.html;


module.exports = Controller.create(Dashboard, {
  enableLoggedOut: true,

  __preload__: function(done) {
    var i = 2;
    function maybeFinish() {
      i--;
      if (!i) {
        done();
      }
    }

    this.iTunesId = this.params['__id__'];
    this.country = navigation.query()['country'] || 'us';

    LKAPIClient.appStoreInfo(this.country, this.iTunesId, {
      onSuccess: function(info, related) {
        this.appInfo = info;
      },
      onError: function() {
        navigation.notFound();
      },
      onComplete: maybeFinish,
      context: this
    });

    LKAPIClient.user({
      onSuccess: function(user) {
        navigation.navigate(this.redirectUrl());
      },
      onComplete: maybeFinish,
      context: this
    });
  },

  redirectUrl: function() {
    var redirectUrl = urls.appendParams('/reviews/dashboard/', {
      'itunes_id': this.iTunesId,
      'country': this.country
    });

    if (navigation.query()['include_related']) {
      redirectUrl = urls.appendParams(redirectUrl, {'include_related': '1'});
    }

    return redirectUrl;
  },

  __body__: function() {
    var signupUrl = urls.appendParams('/signup/', {
      'redirect': this.redirectUrl()
    });

    return {
      content: html({
        app: this.appInfo,
        signupUrl: signupUrl
      })
    };
  }
});
