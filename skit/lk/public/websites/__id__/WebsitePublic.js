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

var Controller = skit.platform.Controller;
var navigation = skit.platform.navigation;
var urls = skit.platform.urls;

var LKAPIClient = library.api.LKAPIClient;
var WebsiteRenderer = library.websites.WebsiteRenderer;
var templatehelpers = library.misc.templatehelpers;


templatehelpers.registerAll();


module.exports = Controller.create({
  __preload__: function(done) {
    var id = this.params['__id__'];

    var path = urls.parse(navigation.url()).path;
    var query = navigation.query();
    if (path.substring(path.length - 1, path.length) != '/') {
      // IMPORTANT: Relative links on this page require a trailing slash.
      navigation.navigate(urls.appendParams(path + '/', query));
      done();
      return;
    }

    this.itunesId = query['itunesId'];
    this.country = query['country'];

    if (id == 'example') {
      LKAPIClient.getExampleWebsite(this.itunesId, this.country, {
        onSuccess: function(website) {
          this.website = website;

          var overridables = {
            'app_name': 'appName',
            'template': 'template',
            'short_description': 'shortDescription',
            'tagline': 'tagline',
            'primary_color': 'primaryColor'
          };

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

          // This lets a user preview the page in the different styles
          // TODO(keith) - should probably only allow this for auth'd owner
          if (query['template']) {
            this.website['template'] = query['template'];
          }
        },
        onError: function() {
          navigation.notFound();
        },
        onComplete: done,
        context: this
      });
    }
  },

  __load__: function() {
    this.renderer = new WebsiteRenderer(this.website);
  },

  __title__: function() {
    return this.renderer.title();
  },

  __meta__: function() {
    return this.renderer.meta();
  },

  __body__: function() {
    return this.renderer.body();
  }
});
