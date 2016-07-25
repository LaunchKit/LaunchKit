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

var Dashboard = library.controllers.Dashboard;
var LKAnalyticsAPIClient = library.api.LKAnalyticsAPIClient;

var html = __module__.html;


module.exports = Controller.create(Dashboard, {
  __preload__: function(done) {
    var appId = navigation.query()['app_id'];
    LKAnalyticsAPIClient.apps(LKAnalyticsAPIClient.Products.SUPER_USERS, {
      onSuccess: function(apps) {
        this.app = iter.find(apps, function(app) {
          return app['id'] == appId;
        });

        if (!this.app) {
          this.app = apps[0] || null;
        }
      },
      onComplete: function() {
        if (!this.app) {
          navigation.notFound();
        }

        done();
      },
      context: this
    });
  },

  __title__: function() {
    return 'Super User Config';
  },

  __body__: function() {
    var name = this.app['name'];
    var freqOptions = LKAnalyticsAPIClient.superUsersFrequencyOptions(this.app['super']['freq']);
    var timeOptions = LKAnalyticsAPIClient.superUsersTimeUsedOptions(this.app['super']['time']);

    return html({
      appName: name,
      freqOptions: freqOptions,
      timeOptions: timeOptions
    });
  },

  __ready__: function() {
    var form = dom.get('#super-user-config-form');
    this.bind(form, 'submit', this.onSubmitForm, this);
  },

  onSubmitForm: function(e) {
    e.preventDefault();

    var form = e.target;
    var params = form.serializeForm();

    var disabled = form.find('button, input, select');
    iter.forEach(disabled, function(el) { el.disable(); });

    var freq = params['freq'];
    var time = params['time'];
    var options = {
      superFreq: freq,
      superTime: time
    };

    LKAnalyticsAPIClient.editAppDetails(this.app['id'], options, {
      onSuccess: function(app) {
        navigation.navigate('/users/dashboard/' + this.app['id'] + '/');
      },
      onError: function() {
        iter.forEach(disabled, function(el) { el.enable(); });
      },
      context: this
    });
  }
});
