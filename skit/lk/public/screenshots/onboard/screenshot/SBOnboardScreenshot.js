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

var ElementWrapper = skit.browser.ElementWrapper;
var dom = skit.browser.dom;
var Controller = skit.platform.Controller;
var iter = skit.platform.iter;
var navigation = skit.platform.navigation;
var net = skit.platform.net;
var string = skit.platform.string;
var urls = skit.platform.urls;
var util = skit.platform.util;
var env = skit.platform.env;

var App = library.controllers.App;
var Dashboard = library.controllers.Dashboard;
var itunessearch = library.misc.itunessearch;
var FilesChooser = library.uploads.FilesChooser;
var devices = library.screenshots.devices;
var uploadui = library.screenshots.uploadui;

var html = __module__.html;
var resultHtml = __module__.result.html;


var SCREENSHOT_FULLSCREEN = '/__static__/images/screenshots/dashboard/preview_only_screenshot.png';
var SCREENSHOT_TEXT_TOP = '/__static__/images/screenshots/dashboard/preview_text_on_top.png';
var SCREENSHOT_TEXT_BOTTOM = '/__static__/images/screenshots/dashboard/preview_text_on_bottom.png';

var ScreenshotFileChooser = uploadui.ScreenshotFileChooser;


module.exports = Controller.create(Dashboard, {
  enableLoggedOut: true,

  __load__: function() {
    var query = navigation.query();
    this.platform = query['platform'];
  },

  __title__: function() {
    return 'Add First Screenshot';
  },

  __body__: function() {
    var selectedScreenshotUrl = SCREENSHOT_FULLSCREEN;

    return {
      content: html({
        selectedScreenshotUrl: selectedScreenshotUrl,
        platform: this.platform,
        layout: this.layout
      })
    };
  },

  __ready__: function() {
    this.rightSection = dom.get('#add-first-screenshot-right');

    this.imageUrlSection = dom.get('#add-first-screenshot-url');
    var imageUrlForm = this.imageUrlSection.get('form');
    this.bind(imageUrlForm, 'submit', this.onSubmitUrl, this);

    if (this.platform != 'Android') {
      var appSearchForm = dom.get('#add-first-screenshot-search form');
      this.bind(appSearchForm, 'submit', this.onSubmitAppSearch, this);

      this.results = dom.get('#add-first-screenshot-results');
      this.delegate(this.results, '[data-itunes-id]', 'click', this.onClickAppResult, this);

      this.delegate(this.rightSection, '[data-screenshot-url]', 'click', this.onClickScreenshotUrl, this);
    }

    this.screenshotFileChooser = new ScreenshotFileChooser(this.rightSection, function(image) {
      this.goNextWithSavedScreenshot(image);
      return true;
    }, this, true);

    var skipStep = dom.get('#skip-step');
    this.bind(skipStep, 'click', this.onClickSkip, this);
  },


  goNextWithSavedScreenshot: function(image) {
    window.sessionStorage['platform'] = this.platform;
    window.sessionStorage['screenshot-id'] = image['id'];
    window.sessionStorage['screenshot-url'] = image['imageUrls']['full'];

    var nextUrl = urls.appendParams('/screenshots/onboard/layout/', {
      'platform': this.platform,
      'orientation': (image.width > image.height) ? 'landscape' : 'portrait'
    });
    navigation.navigate(nextUrl);
  },


  // CHOOSE URL

  onSubmitUrl: function(evt) {
    evt.preventDefault();
    this.rightSection.addClass('adding-image-url');

    var urlPreview = this.imageUrlSection.get('.url-preview');
    var urlForm = this.imageUrlSection.get('form.load-url');

    urlPreview.addClass('loading');
    urlPreview.removeClass('error');
    urlPreview.removeClass('success');

    var maybeImageUrl = string.trim(evt.target.get('input[type=url]').value());

    var error = function() {
      urlPreview.removeClass('loading');
      urlPreview.addClass('error');
    };

    var img = new Image();
    img.crossOrigin = 'Anonymous';
    img.onerror = error;
    img.onload = function() {
      urlPreview.removeClass('loading');

      if (!img.width) {
        error();
      } else {
        urlForm.addClass('hidden');
        urlPreview.addClass('success');
        urlPreview.removeClass('error');
      }
    };

    img.src = maybeImageUrl;
    var toReplace = urlPreview.get('.screenshot-url-preview img').element;
    toReplace.parentNode.insertBefore(img, toReplace);
    toReplace.parentNode.removeChild(toReplace);

    // Make both of these things clickable.
    var $img = new ElementWrapper(img);
    $img.setData('screenshot-url', maybeImageUrl);
    urlPreview.get('button').setData('screenshot-url', maybeImageUrl);
  },


  // APP STORE SEARCH

  onSubmitAppSearch: function(evt) {
    evt.preventDefault();

    this.rightSection.addClass('searching');

    var query = evt.target.get('input[type=text]').value();
    this.lastQuery = query;

    this.results.addClass('loading');

    this.appsById = this.appsById || {};

    itunessearch.findApps('us', query, function(resultsQuery, results) {
      if (resultsQuery != this.lastQuery || !results) {
        return;
      }

      results = results.slice(0, 10);
      iter.forEach(results, function(result) {
        this.appsById[result['iTunesId']] = result;
      }, this);

      this.results.removeClass('loading');
      this.results.element.innerHTML = iter.map(results, function(r) {
        return resultHtml(r);
      }).join('');
    }, this, {ipad: false, mac: false});
  },

  onClickAppResult: function(evt) {
    evt.preventDefault();

    var row = evt.currentTarget.up('.result');
    var expanded = row.hasClass('expanded');
    if (expanded) {
      row.removeClass('expanded');
      return;
    }

    iter.forEach(row.parent().find('.expanded'), function($r) {
      $r.removeClass('expanded');
    });

    var iTunesId = row.getData('itunes-id');
    var app = this.appsById[iTunesId];

    var imgs = row.find('img[data-screenshot-url]');
    iter.forEach(imgs, function($img) {
      $img.element.src = $img.getData('screenshot-url');
    });

    row.addClass('expanded');
  },

  onClickScreenshotUrl: function(evt) {
    evt.preventDefault();

    var url = evt.currentTarget.getData('screenshot-url');
    uploadui.uploadImageUrl(url, function(image) {
      this.goNextWithSavedScreenshot(image);
    }, this);
  },

  onClickSkip: function(evt) {
    evt.preventDefault();

    var shotURL;
    if (env.get('debug')) {
      shotURL = document.location.origin + SCREENSHOT_FULLSCREEN;
    } else {
      shotURL = SCREENSHOT_FULLSCREEN;
    }

    uploadui.uploadImageUrl(shotURL, function(image) {
      this.goNextWithSavedScreenshot(image);
    }, this);
  }
});
