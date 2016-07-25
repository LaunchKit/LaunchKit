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
var Handlebars = skit.thirdparty.handlebars;

var LKAPIClient = library.api.LKAPIClient;
var colors = library.misc.colors;
var Dashboard = library.controllers.Dashboard;
var uploadui = library.screenshots.uploadui;
var WebsiteRenderer = library.websites.WebsiteRenderer;
var templates = library.websites.templates;
var ColorThief = third_party.ColorThief;

var html = __module__.html;


Handlebars.registerHelper('previewLink', function(websiteId, template) {
  var params = navigation.query();
  params['template'] = template;
  return urls.appendParams('/websites/' + websiteId, params);
});


module.exports = Controller.create(Dashboard, {
  enableLoggedOut: true,

  __preload__: function(done) {
    var id = this.params['__id__'];

    var query = navigation.query();
    this.itunesId = query['itunesId'];
    this.country = query['country'];

    var overridables = {
      'app_name': 'appName',
      'short_description': 'shortDescription',
      'tagline': 'tagline',
      'primary_color': 'primaryColor'
    };

    if (id == 'example') {
      LKAPIClient.getExampleWebsite(this.itunesId, this.country, {
        onSuccess: function(website) {
          this.website = website;

          for (var key in overridables) {
            if (query[key]) {
              this.website[overridables[key]] = query[key];
            }
          }
        },
        onError: function() {
          navigation.notFound();
        },
        onComplete: done,
        context: this
      });

    } else {
      LKAPIClient.getWebsite(id, {
        onSuccess: function(website) {
          this.website = website;
        },
        onError: function() {
          navigation.notFound();
        },
        onComplete: done,
        context: this
      });

    }
  },

  __title__: function() {
    return 'Change ' + this.website['appName'] + ' Template';
  },

  __body__: function() {
    return {
      content: html({
        website: this.website,
        templates: templates.TEMPLATES,
        isExample: this.website['id'] == 'example'
      })
    };
  },

  __ready__: function() {
    this.setupColorOptions();
    this.setupIFrames();
  },

  setupColorOptions: function() {
    var $holder = dom.get('#palette-holder');
    if (!$holder) {
      return;
    }

    var ct = new ColorThief();
    var image = new Image();
    image.crossOrigin = 'Anonymous';
    image.onload = util.bind(function() {
      var palette = ct.getPalette(image, 6);
      var params = navigation.query();
      iter.forEach(palette, function(rgbArray) {
        var hex = colors.rgbToHex(rgbArray);
        var div = document.createElement('div');
        div.style.backgroundColor = hex;
        if (params['primary_color'] === hex) {
          div.className = 'palette-choice palette-selected';
        } else {
          div.className = 'palette-choice';
        }
        div.onclick = function(evt) {
          var nextUrl = urls.appendParams(navigation.relativeUrl(), {'primary_color': hex});
          navigation.navigate(nextUrl);
        };
        $holder.append(div);
      }, this);
    }, this);
    image.src = this.website['images']['icon']['url'];
  },

  setupIFrames: function() {
    var iframes = dom.find('iframe[data-template-id]');
    var template = this.website['template'];
    iter.forEach(iframes, function($iframe) {
      this.website['template'] = $iframe.getData('template-id');
      var renderer = new WebsiteRenderer(this.website);
      renderer.renderInIframe($iframe);
    }, this);
    this.website['template'] = template;
  },

  handleAction: function(action, $target) {
    switch(action) {
      case 'choose':
        if (!this.user) {
          this.redirectToLogin();
          return;
        }

        if (this.choosing) {
          return;
        }
        this.choosing = true;

        var done = util.bind(function() {
          delete this.choosing;
        }, this);

        var template = $target.getData('template');
        if (this.website.id != 'example') {
          this.saveTemplate(template, done);
        } else {
          this.createWebsiteWithTemplate(template, done);
        }

        break;
    }
  },

  saveTemplate: function(template, done) {
    LKAPIClient.editWebsite(this.website['id'], {'template': template}, {
      onSuccess: function(website) {
        this.reload();
      },
      onComplete: done,
      context: this
    });
  },

  createWebsiteWithTemplate: function(template, done) {
    if (!this.itunesId) {
      this.createWebsiteWithTemplateAndImages(template, '', [], done);
      return;
    }

    var images = this.website['images'];
    var iconUrl = images['icon'] && images['icon']['url'];
    var screenshotUrls = iter.map(images['screenshots']['iPhone'], function(screenshot) {
      return screenshot['url'];
    });

    uploadui.uploadWebsiteImages(iconUrl, screenshotUrls, function(iconImage, screenshotImages) {
      var screenshotIds = iter.map(screenshotImages, function(image) { return image['id']; });
      this.createWebsiteWithTemplateAndImages(template, iconImage && iconImage['id'], screenshotIds, done);
    }, this);
  },

  createWebsiteWithTemplateAndImages: function(template, iconId, screenshotIds, done) {
    var params = navigation.query();
    delete params['itunesId'];

    params['template'] = template;
    params['icon_id'] = iconId;
    params['itunes_id'] = this.itunesId;
    params['country'] = this.country;
    params['iphone_screenshot_ids'] = screenshotIds.join(',');

    LKAPIClient.createWebsite(params, {
      onSuccess: function(website) {
        navigation.navigate('/websites/dashboard/' + website['id'] + '/edit/');
      },
      onComplete: done,
      context: this
    });
  }
});
