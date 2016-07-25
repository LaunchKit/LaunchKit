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
var navigation = skit.platform.navigation;
var iter = skit.platform.iter;
var urls = skit.platform.urls;
var util = skit.platform.util;

var AmbiguousProgressOverlay = library.overlays.AmbiguousProgressOverlay;
var LKAPIClient = library.api.LKAPIClient;
var LKConfigAPIClient = library.api.LKConfigAPIClient;
var Dashboard = library.controllers.Dashboard;

var html = __module__.html;


module.exports = Controller.create(Dashboard, {
  enableLoggedOut: false,
  preferSignupNotLogin: true,

  floatingBoxClass: 'huge-box',

  __preload__: function(done) {
    var query = navigation.query();
    this.iTunesId = query['itunes_id'];
    this.country = query['country'] || 'us';
    LKAPIClient.appStoreInfo(this.country, this.iTunesId, {
      onSuccess: function(info) {
        this.appInfo = info;
      },
      onError: function() {
        navigation.notFound();
      },
      onComplete: done,
      context: this
    });
  },

  __load__: function() {
    var sellerURL = this.appInfo['developer']['url'];
    var email = '';
    if (sellerURL) {
      email = 'support@' + urls.parse(sellerURL).host;
    }

    var iTunesURL = 'https://itunes.apple.com/' + this.country + '/app/id' + this.appInfo['iTunesId'];
    var iTunesId = this.appInfo['iTunesId'];
    var latestVersion = this.appInfo['version'];

    this.exampleRules = [
      {key: 'iTunesId',  kind: 'int', value: iTunesId, description: 'iTunes ID'},
      {key: 'iTunesURL',  kind: 'string', value: iTunesURL, description: 'iTunes download URL'},
      {
        key: 'isOlderVersion',
        kind: 'bool',
        value: 'true',
        description: 'Shows if user is using latest app version',
        select: true,
        additionalRule: {
          version: latestVersion,
          match: '>=',
          value: 'false'
        }
      },
      {key: 'websiteURL', kind: 'string', value: sellerURL, description: 'App website'},
      {key: 'supportEmail',  kind: 'string', value: email, description: 'Email address for support'},
      {key: 'twitterHandle',  kind: 'string', value: '', description: 'Twitter @username for the app'}
    ];
  },

  __title__: function() {
    return 'Confirm App';
  },

  __body__: function() {
    return {
      content: html({
        app: this.appInfo,
        country: this.country,
        exampleRules: this.exampleRules
      })
    };
  },

  __ready__: function() {
    var form = dom.get('#config-form');
    this.bind(form, 'submit', this.onSubmitForm, this);
  },

  onSubmitForm: function(e) {
    e.preventDefault();

    var spinner = new AmbiguousProgressOverlay();
    spinner.show();

    var formData = e.target.serializeForm();
    var ruleOptions = [];
    iter.forEach(this.exampleRules, function(rule) {
      ruleOptions.push({
        key: rule.key,
        kind: rule.kind,
        value: rule.key in formData ? formData[rule.key] : rule.value,
        description: formData[rule.key + '-description'],
        bundleId: this.appInfo['bundleId']
      });

      if (rule.additionalRule) {
        var matchToAPIMatch = {
          '>': 'gt',
          '>=': 'gte',
          '=': 'eq',
          '<=': 'lte',
          '<': 'lt'
        };

        ruleOptions.push({
          key: rule.key,
          value: rule.additionalRule.value,
          bundleId: this.appInfo['bundleId'],
          version: rule.additionalRule.version,
          versionMatch: matchToAPIMatch[rule.additionalRule.match]
        });
      }
    }, this);

    var total = ruleOptions.length;

    var sendNext = util.bind(function() {
      spinner.setProgressPercent(100.0 * ((total - ruleOptions.length) / total));

      if (!ruleOptions.length) {
        var nextUrl = urls.appendParams('/config/onboard/3-extras/', {
          'bundle_id': this.appInfo['bundleId']
        });
        navigation.navigate(nextUrl);
        return;
      }

      var rule = ruleOptions.shift();
      LKConfigAPIClient.createRule(rule, {
        onComplete: function() {
          setTimeout(sendNext, 0.2);
        },
        context: this
      });
    }, this);

    sendNext();
  }
});
