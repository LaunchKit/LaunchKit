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
var object = skit.platform.object;
var urls = skit.platform.urls;
var util = skit.platform.util;

var LKAnalyticsAPIClient = library.api.LKAnalyticsAPIClient;
var Dashboard = library.controllers.Dashboard;

var html = __module__.html;


module.exports = Controller.create(Dashboard, {
  // OVERRIDE THINGS

  showSuperConfig: true,
  showConfigChildren: false,
  getAppId: function(cb) {
    cb(null);
  },
  getBackUrl: function() {
    throw new Error('Implement getBackUrl()');
  },

  // INTERNAL THINGS

  __preload__: function(done) {
    this.getAppId(util.bind(function(appId) {
      if (appId === null) {
        throw new Error('Add method for finding the current app ID or bundle');
      }

      LKAnalyticsAPIClient.appWithId(appId, {
        onSuccess: function(app) {
          this.app = app;
        },
        onError: function() {
          navigation.notFound();
        },
        onComplete: done,
        context: this
      });
    }, this));
  },

  __title__: function() {
    return 'Edit ' + this.app['names']['short'];
  },

  __body__: function() {
    var freqOptions = LKAnalyticsAPIClient.superUsersFrequencyOptions(this.app['super'] && this.app['super']['freq']);
    var timeOptions = LKAnalyticsAPIClient.superUsersTimeUsedOptions(this.app['super'] && this.app['super']['time']);

    return html({
      app: this.app,
      showSuperConfig: this.showSuperConfig,
      showConfigChildren: this.showConfigChildren,
      freqOptions: freqOptions,
      timeOptions: timeOptions,
      backUrl: this.getBackUrl()
    });
  },

  __ready__: function() {
    this.bind(dom.get('#app-info-edit-form'), 'submit', this.onSubmitForm, this);

    var addChildForm = dom.get('#app-edit-add-child');
    if (addChildForm) {
      this.bind(addChildForm, 'submit', this.onSubmitAddChildForm, this);
    }
  },

  handleAction: function(action, $target) {
    Dashboard.prototype.handleAction.apply(this, arguments);

    switch (action) {
      case 'remove-config-child':
        var childId = $target.up('[data-id]').getData('id');
        this.removeConfigChild(childId);
        break;

    }
  },

  removeConfigChild: function(childId) {
    if (this.removingChild) {
      return;
    }
    this.removingChild = true;

    var options = {
      configParentId: ''
    };

    LKAnalyticsAPIClient.editAppDetails(childId, options, {
      onSuccess: function() {
        this.reload();
      },
      onComplete: function() {
        delete this.removingChild;
      },
      context: this
    });
  },

  onSubmitAddChildForm: function(e) {
    e.preventDefault();

    var params = e.target.serializeForm();
    var options = {
      bundleId: params['bundle_id'],
      configParentId: this.app['id']
    };

    var $toDisable = e.target.find('input, button, select');
    LKAnalyticsAPIClient.createAppWithOptions(options, {
      onSuccess: function() {
        this.reload();
      },
      onError: function() {
        iter.forEach($toDisable, function($i) { $i.enable(); });
      },
      context: this
    });
  },

  onSubmitForm: function(e) {
    e.preventDefault();

    var params = e.target.serializeForm();
    var options = {
      name: params['name']
    };

    if ('freq' in params) {
      options.superFreq = params['freq'];
      options.superTime = params['time'];
    }

    var $toDisable = e.target.find('input, button, select');
    iter.forEach($toDisable, function($i) { $i.disable(); });

    LKAnalyticsAPIClient.editAppDetails(this.app['id'], options, {
      onSuccess: function() {
        var backUrl = urls.appendParams(this.getBackUrl(), {'edited': '1'});
        navigation.navigate(backUrl);
      },
      onError: function() {
        iter.forEach($toDisable, function($i) { $i.enable(); });
      },
      context: this
    });
  }
});
