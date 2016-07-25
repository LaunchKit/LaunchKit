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

var LKAnalyticsAPIClient = library.api.LKAnalyticsAPIClient;
var Dashboard = library.controllers.Dashboard;


module.exports = Controller.create(Dashboard, {
  enableLoggedOut: false,
  preferSignupNotLogin: true,

  __preload__: function(done) {
    var params = navigation.query();
    var options = {
      iTunesId: params['itunes_id'],
      iTunesCountry: params['country'],
      product: LKAnalyticsAPIClient.Products.SUPER_USERS
    };

    LKAnalyticsAPIClient.createAppWithOptions(options, {
      onSuccess: function(app) {
        var url = urls.appendParams('/users/onboard/superuser-profile/', {'app_id': app['id']});
        navigation.navigate(url);
      },
      onError: function() {
        navigation.navigate('/users/onboard/?error=1');
      },
      onComplete: done,
      context: this
    });
  }
});
