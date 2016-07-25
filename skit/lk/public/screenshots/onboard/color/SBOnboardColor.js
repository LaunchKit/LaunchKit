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
var devices = library.screenshots.devices;
var ScreenshotFormWrapper = library.screenshots.ScreenshotFormWrapper;
var ScreenshotCanvasWrapper = library.screenshots.ScreenshotCanvasWrapper;
var fonts = library.screenshots.fonts;

var html = __module__.html;


module.exports = Controller.create(Dashboard, {
  enableLoggedOut: true,

  __load__: function() {
    var query = navigation.query();
    this.platform = query['platform'] || 'iOS';
    this.layout = query['layout'] || 'below';
    this.orientation = query['orientation'] || 'portrait';
  },

  __title__: function() {
    return 'Choose a Device Color';
  },

  __body__: function() {
    var platform = devices.platforms[this.platform];
    var phone = platform.devices.byName[platform.defaultDevice];
    var colors = [{
      value: 'white',
      name: 'White Device'
    },{
      value: 'black',
      name: 'Black Device'
    },{
      value: 'gold',
      name: 'Gold Device',
      requiresPro: true
    },{
      value: 'rose',
      name: 'Rose Device',
      requiresPro: true
    }];

    return {
      content: html({
        phone: phone,
        dimensions: phone[this.orientation],
        layout: this.layout,
        colors: colors
      }),
    };
  },

  __ready__: function() {
    var imageUrl = window.sessionStorage['screenshot-url'];
    this.canvasWrappers = devices.screenshotCanvasWrappersInContainer(dom.get('body'), this.platform, this.orientation);

    iter.forEach(this.canvasWrappers, function(canvasWrapper) {
      canvasWrapper.setScreenshotImageWithUrl(imageUrl);
      canvasWrapper.setFontSize(5);
      canvasWrapper.setFontWeight('Lora', '400');
      canvasWrapper.setLabel('You can set this label to anything you want!');
      canvasWrapper.setFontColor('#333333');
    }, this);
  },

  handleAction: function(name, $target) {
    Dashboard.prototype.handleAction.call(this, name, $target);

    var nextUrl = urls.appendParams('/screenshots/onboard/styles/', {
      'platform': this.platform,
      'layout': this.layout,
      'phoneColor': name,
      'orientation': this.orientation
    });
    navigation.navigate(nextUrl);

  },

});
