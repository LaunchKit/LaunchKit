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
var urls = skit.platform.urls;

var LKAnalyticsAPIClient = library.api.LKAnalyticsAPIClient;
var AddCustomSDKApp = library.controllers.onboarding.AddCustomSDKApp;


module.exports = Controller.create(AddCustomSDKApp, {
  productTag: LKAnalyticsAPIClient.Products.CONFIG,
  cancelUrl: '/config/',
  nextUrl: '/config/onboard/3-extras/',
  nextUrlWithApp: function(app) {
    return urls.appendParams(this.nextUrl, {'bundle_id': app['bundleId']});
  }
});
