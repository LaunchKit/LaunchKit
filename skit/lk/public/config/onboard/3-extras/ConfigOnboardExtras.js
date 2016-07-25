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
var util = skit.platform.util;

var LKConfigAPIClient = library.api.LKConfigAPIClient;
var Dashboard = library.controllers.Dashboard;
var AmbiguousProgressOverlay = library.overlays.AmbiguousProgressOverlay;

var html = __module__.html;


var trueFalseValues = [{value: '1', label: 'true'}, {value: '0', label: 'false'}];
var examples = [
  {
    title: 'Do you use <strong>iRate</strong>?',
    subtext: 'You can control when iRate prompts for reviews and whether it is enabled from the cloud.',
    rules: [
      {key: 'enableiRate',  kind: 'bool', value: 'true', selectValues: trueFalseValues, description: 'Controls whether iRate is enabled'},
      {key: 'daysUntilPrompt',  kind: 'int', value: 5, description: 'Number of days until iRate asks for review'},
      {key: 'usesUntilPrompt',  kind: 'int', value: 15, description: 'Number of app opens until iRate asks for review'}
    ]
  },
  {
    title: 'Do you <strong>upload photos?</strong>',
    subtext: 'You can change the size or quality of your photo uploads later if your requirements change.',
    rules: [
      {key: 'uploadPhotoWidth',  kind: 'int', value: 2048, description: 'Size of photo in pixels to upload'},
      {key: 'uploadPhotoQuality',  kind: 'float', value: 0.80, description: 'JPEG quality of photo to upload'}
    ]
  },
  {
    title: 'Do you upload <strong>video</strong>?',
    subtext: 'You can change the allowed duration or video quality of uploads in case you want to change this later.',
    rules: [
      {key: 'uploadVideoDuration',  kind: 'int', value: 120, description: 'Duration of video in seconds allowed'},
      {key: 'uploadVideoFormat',  kind: 'string', value: '720p', description: 'Format and size of video to upload'}
    ]
  },
  {
    title: 'Are you launching a new feature soon?',
    subtext: 'You can disable it here and enable it later, or just for certain builds.',
    rules: [
      {key: 'enableNewFeature',  kind: 'bool', selectValues: trueFalseValues, description: 'Whether the new feature is enabled'}
    ]
  }
];


module.exports = Controller.create(Dashboard, {
  floatingBoxClass: 'huge-box',

  __load__: function() {
    var query = navigation.query();
    this.bundleId = query['bundle_id'];
  },

  __title__: function() {
    return 'Cloud Config: Examples';
  },

  __body__: function() {
    var nextUrl = '/config/dashboard/' + encodeURIComponent(this.bundleId) + '/';

    return html({
      examples: examples,
      nextUrl: nextUrl
    });
  },

  __ready__: function() {
    iter.forEach(dom.find('.config-form'), function(form) {
      this.bind(form, 'submit', this.onSubmitForm, this);
    }, this);
  },

  handleAction: function(action, $target) {
    Dashboard.prototype.handleAction.apply(this, arguments);

    if (action == 'cancel-rules') {
      iter.forEach($target.up('form').find('input, button, select'), function(el) {
        el.disable();
      });
    }
  },

  onSubmitForm: function(e) {
    e.preventDefault();

    var formData = e.target.serializeForm();
    iter.forEach(e.target.find('input, button, select'), function(el) {
      el.disable();
    });
    e.target.get('button[type=submit]').setText('Added!');

    var ruleOptions = [];
    for (var k in formData) {
      var value = formData[k];
      var description = formData[k + '-description'];
      var kind = formData[k + '-kind'];
      if (!kind) {
        continue;
      }

      ruleOptions.push({
        key: k,
        kind: kind,
        value: value,
        description: description,
        bundleId: this.bundleId
      });
    }

    var total = ruleOptions.length;
    var sendNext = util.bind(function() {
      if (!ruleOptions.length) {
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
