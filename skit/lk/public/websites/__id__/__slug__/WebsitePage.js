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

var LKAPIClient = library.api.LKAPIClient;
var WebsiteRenderer = library.websites.WebsiteRenderer;
var templatehelpers = library.misc.templatehelpers;


templatehelpers.registerAll();


module.exports = Controller.create({
  __preload__: function(done) {
    var id = this.params['__id__'];
    var slug = this.params['__slug__'];

    var query = navigation.query();
    var templateOverride = query['template'];

    LKAPIClient.getWebsitePage(id, slug, {
      onSuccess: function(website, page) {
        this.website = website;
        this.page = page;

        if (templateOverride) {
          this.website['template'] = templateOverride;
        }
      },
      onError: function() {
        navigation.notFound();
      },
      onComplete: done,
      context: this
    });
  },

  __load__: function() {
    this.renderer = new WebsiteRenderer(this.website, this.page);
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
