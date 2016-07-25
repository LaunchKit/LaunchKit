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
var cookies = skit.platform.cookies;
var navigation = skit.platform.navigation;
var urls = skit.platform.urls;

var SDKDocs = library.controllers.sdk.SDKDocs;

var html = __module__.html;
var emailHtml = __module__.email.html;


function installUrl(accessToken) {
  var params = {
    'token': accessToken
  };
  return urls.appendParams('https://yourdomain.com/sdk/share/', params);
}


function installEmailUrl(accessToken) {
  var body = emailHtml({
    installUrl: installUrl(accessToken)
  });

  return urls.appendParams('mailto:', {
    subject: 'Need your help installing an SDK',
    body: body
  });
}


module.exports = Controller.create(SDKDocs, {
  __preload__: function(done) {
    var query = navigation.query();
    var nextUrl =  this.redirectUrl('/sdk/install/');

    if (query['unset']) {
      cookies.set(this.TOKEN_COOKIE_NAME, null);
      navigation.navigate(nextUrl);
      done();
      return;
    }

    if (query['token']) {
      cookies.set(this.TOKEN_COOKIE_NAME, query['token']);
      navigation.navigate(nextUrl);
      done();
      return;
    }

    if (!this.user) {
      this.redirectToLogin();
      done();
      return;
    }

    done();
  },

  __body__: function() {
    return html({
      installUrl: installUrl(this.token),
      installEmailUrl: installEmailUrl(this.token)
    });
  }
});