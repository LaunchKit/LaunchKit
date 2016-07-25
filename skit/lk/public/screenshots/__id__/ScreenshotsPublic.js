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
var util = skit.platform.util;

var LKAPIClient = library.api.LKAPIClient;
var Base = library.controllers.Base;
var ScreenshotCanvasWrapper = library.screenshots.ScreenshotCanvasWrapper;
var phones = library.screenshots.phones;
var devices = library.screenshots.devices;
var AsyncTask = library.tasks.AsyncTask;
var AsyncTaskQueue = library.tasks.AsyncTaskQueue;
var bootstrap = library.misc.bootstrap;

var html = __module__.html;
var meta = __module__.meta.html;


module.exports = Controller.create(Base, {
  enableLoggedOut: true,

  __preload__: function(done) {
    LKAPIClient.screenshotSetAndShots(this.params['__id__'], {
      onSuccess: function(set, shots) {
        this.set = set;
        this.shots = shots;
      },
      onError: function() {
        navigation.notFound();
      },
      onComplete: done,
      context: this
    });
  },

  __load__: function() {
    var platform = devices.platforms[this.set.platform];
    var configs = [];
    var allPhones = platform.devices.byType['phone'];

    var configsByPhone = [];
    iter.forEach(allPhones, function(phone) {
      var group = [];
      var groupConfig = {phone: phone, configs: group};

      iter.forEach(this.shots, function(shot, i) {
        var filename = phone.filenamePrefix + ' - Screenshot ' + (i + 1);
        var config = {
          phone: phone,
          shot: shot,
          filename: filename,
          dimensions: phone['portrait']
        };

        group.push(config);
        configs.push(config);
      });

      // only show devices that have shots
      if (group.length) {
        configsByPhone.push(groupConfig);
      }
    }, this);

    this.configsByPhone = configsByPhone;
    this.configs = configs;
  },

  __title__: function() {
    if (this.set.platform == 'Android') {
      return 'App Store screenshots for ' + this.set['name'] + ' ' + this.set['version'];
    } else {
      return 'App Store screenshots for ' + this.set['name'] + ' ' + this.set['version'];
    }
  },

  __meta__: function() {
    return meta({
      set: this.set
    });
  },

  __body__: function() {
    return html({
      set: this.set,
      configsByPhone: this.configsByPhone
    });
  },


  __ready__: function() {
    var containers = dom.find('#screenshot-set > ul > li');
    var wrappers = [];
    iter.forEach(containers, function(container, i) {
      var config = this.configs[i];

      var shot = config.shot;
      var phone = config.phone;

      var canvasWrapper = new ScreenshotCanvasWrapper(phone, container.get('.screenshot-canvas-container'));
      canvasWrapper.setScreenshotImageWithUrl(shot['screenshot']['imageUrls']['full']);
      if (shot['background']) {
        canvasWrapper.setBackgroundImageWithUrl(shot['background']['imageUrls']['full']);
      }

      canvasWrapper.setLabel(shot['label']);
      canvasWrapper.setLabelPosition(shot['labelPosition']);
      canvasWrapper.setPhoneColor(shot['phoneColor']);

      canvasWrapper.setFontWeight(shot['font'], shot['fontWeight']);
      canvasWrapper.setFontSize(shot['fontSize']);
      canvasWrapper.setFontColor(shot['fontColor']);

      canvasWrapper.setBackgroundColor(shot['backgroundColor']);

      wrappers.push(canvasWrapper);
    }, this);

    // NOTE: It is important that this array and the configs array
    // are in the same order.
    this.canvasWrappers = wrappers;
  }
});
