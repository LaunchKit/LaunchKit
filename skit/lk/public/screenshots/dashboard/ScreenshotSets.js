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
var Dashboard = library.controllers.Dashboard;
var DuplicateSetOverlay = library.screenshots.DuplicateSetOverlay;
var introHtml = library.products.dashboardintro;
var scripts = library.misc.scripts;

var html = __module__.html;



module.exports = Controller.create(Dashboard, {
  __preload__: function(done) {
    LKAPIClient.screenshotSets({
      onSuccess: function(sets) {
        this.sets = sets;
      },
      onComplete: done,
      context: this
    });
  },

  __load__: function() {
    this.tweetUpsell = !!navigation.query()['exported'];
  },

  __title__: function() {
    return 'Screenshot Sets';
  },

  __body__: function() {
    if (!this.sets.length) {
      return introHtml({product: this.product});
    }

    return html({
      sets: this.sets,
      tweetUpsell: this.tweetUpsell
    });
  },

  handleAction: function(name, $target) {
    Dashboard.prototype.handleAction.call(this, name, $target);

    switch (name) {
      case 'maybe-duplicate-set':
        var set_index = $target.getData('set-index');
        this.maybeDuplicateSet(set_index);
        break;

      case 'maybe-create-set':
        navigation.navigate($target.element.href);
        break;
    }
  },

  maybeDuplicateSet: function(index) {
    var duplicate = new DuplicateSetOverlay(this.sets[index]);
    duplicate.show();
  }

});
