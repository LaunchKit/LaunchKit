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
var Handlebars = skit.thirdparty.handlebars;

var LKAPIClient = library.api.LKAPIClient;
var Dashboard = library.controllers.Dashboard;
var WebsiteRenderer = library.websites.WebsiteRenderer;
var introHtml = library.products.dashboardintro;

var html = __module__.html;


module.exports = Controller.create(Dashboard, {
  __preload__: function(done) {
    LKAPIClient.getAllWebsites({
      onSuccess: function(websites) {
        this.websites = websites;
      },
      onComplete: function() {
        done();
      },
      context: this
    });
  },

  __title__: function() {
    return this.product.name + ' Dashboard';
  },

  __body__: function() {
    var bodyHtml;

    if (this.websites.length) {
      var tweetUpsell = navigation.query()['saved'];

      bodyHtml = html({
        tweetUpsell: tweetUpsell,
        websites: this.websites
      });
    } else {
      bodyHtml = introHtml({product: this.product});
    }

    return {
      content: bodyHtml
    };
  },

  __ready__: function() {
    var websitesById = {};
    iter.forEach(this.websites, function(website) {
      websitesById[website['id']] = website;
    });

    var iframes = dom.find('iframe[data-website-id]');
    iter.forEach(iframes, function($iframe) {
      var website = websitesById[$iframe.getData('website-id')];

      var renderer = new WebsiteRenderer(website);
      renderer.renderInIframe($iframe);
    });
  }
});
