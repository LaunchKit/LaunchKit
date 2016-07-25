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
var events = skit.browser.events;
var Controller = skit.platform.Controller;
var iter = skit.platform.iter;
var object = skit.platform.object;
var navigation = skit.platform.navigation;
var urls = skit.platform.urls;
var util = skit.platform.util;

var LKAPIClient = library.api.LKAPIClient;
var WebsiteRenderer = library.websites.WebsiteRenderer;
var googleanalytics = library.misc.googleanalytics;
var templatehelpers = library.misc.templatehelpers;
var cachedloader = library.websites.cachedloader;


templatehelpers.registerAll();


var CUSTOM_TRACKER_NAME = 'user';
var YOUR_GA_ID = 'UA-XXXXXXXX-X';


module.exports = Controller.create({
  __preload__: function(done) {
    var slug = this.params['__slug__'];
    cachedloader.loadForCurrentDomainSlug(slug, function(domain, website, page) {
      this.domain = domain;
      this.website = website;
      this.page = page || null;

      var found = !!this.website;
      if (slug) {
        found = !!this.page;
      }

      if (!found) {
        navigation.notFound();
      }

      done();
    }, this);
  },

  __load__: function() {
    this.renderer = new WebsiteRenderer(this.website, this.page);
    this.customAnalyticsId = this.website['googleAnalyticsId'];
  },

  __title__: function() {
    return this.renderer.title();
  },

  __meta__: function() {
    return this.renderer.meta();
  },

  __body__: function() {
    return this.renderer.body(true);
  },

  __ready__: function() {
    // Setup global GA for us.
    googleanalytics.create(YOUR_GA_ID);
    googleanalytics.trackPageview();

    // Setup GA for pro users who have it enabled.
    if (this.customAnalyticsId) {
      googleanalytics.create(this.customAnalyticsId, CUSTOM_TRACKER_NAME);
      googleanalytics.trackPageview(CUSTOM_TRACKER_NAME);
    }

    var path = urls.parse(navigation.url()).path;
    LKAPIClient.trackWebsiteView(
        this.website['id'],
        this.domain,
        navigation.referer(),
        navigation.userAgent(),
        path);

    events.delegate(dom.get('body'), 'a[href]', 'click', this.onClickLink, this);
  },

  onClickLink: function(evt) {
    var href = evt.currentTarget.element.href;
    if (evt.metaKey || !href) {
      return;
    }
    // let's track this, then follow the link.
    evt.preventDefault();

    var timeout;
    function doNext() {
      clearTimeout(timeout);
      navigation.navigate(href);
    }
    timeout = setTimeout(function() {
      util.log('GA tracking timeout');
      doNext();
    }, 2000);

    var options = {
      'eventCategory': 'Link',
      'eventAction': 'click',
      'eventLabel': href
    };

    if (this.customAnalyticsId) {
      googleanalytics.trackEvent(options, CUSTOM_TRACKER_NAME);
    }

    var newOptions = object.copy(options);
    newOptions['hitCallback'] = doNext;
    googleanalytics.trackEvent(newOptions);
  }
});
