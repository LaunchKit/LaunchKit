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

var LKAPIClient = library.api.LKAPIClient;
var Dashboard = library.controllers.Dashboard;

var html = __module__.html;


module.exports = Controller.create(Dashboard, {
  enableLoggedOut: true,

  __preload__: function(done) {
    var appstoreId = this.params['__id__'];
    this.country = navigation.query()['country'] || 'us';
    LKAPIClient.appStoreInfo(this.country, appstoreId, {
      onSuccess: function(info, related) {
        this.appInfo = info;
        this.related = related;
      },
      onError: function() {
        navigation.notFound();
      },
      onComplete: done,
      context: this
    });
  },

  __title__: function() {
    return 'Confirm App';
  },

  __body__: function() {
    return html({
      app: this.appInfo,
      related: this.related,
      country: this.country
    });
  }
});
