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

var html = __module__.html;


module.exports = Controller.create(Dashboard, {
  // TO OVERRIDE

  productTag: '', // eg. LKAnalyticsAPIClient.Products.RELEASE_NOTES
  cancelUrl: '/',
  nextUrl: '/',
  nextUrlWithApp: function(app) {
    return urls.appendParams(this.nextUrl, {'app_id': app['id']});
  },


  // PRIVATE

  enableLoggedOut: false,
  preferSignupNotLogin: true,

  __title__: function() {
    return 'Add Custom App';
  },

  __body__: function() {
    var query = navigation.query();
    var name = query['name'];
    var bundleId = query['bundle_id'];
    return html({
      name: name,
      bundleId: bundleId,
      cancelUrl: this.cancelUrl
    });
  },

  __ready__: function() {
    var form = dom.get('#app-info-confirm-form');
    this.bind(form, 'submit', this.onSubmitForm, this);
  },

  onSubmitForm: function(e) {
    e.preventDefault();

    var form = e.target;
    var params = form.serializeForm();

    var disabled = form.find('button, input');
    iter.forEach(disabled, function(el) { el.disable(); });

    var options = {
      name: params['name'],
      bundleId: params['bundle_id'],
      product: this.productTag
    };

    LKAnalyticsAPIClient.createAppWithOptions(options, {
      onSuccess: function(app) {
        var url = this.nextUrlWithApp(app);
        navigation.navigate(url);
      },
      onError: function() {
        iter.forEach(disabled, function(el) { el.enable(); });
      },
      context: this
    });
  }
});
