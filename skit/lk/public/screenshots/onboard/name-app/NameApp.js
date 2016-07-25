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

var LKAPIClient = library.api.LKAPIClient;
var Dashboard = library.controllers.Dashboard;
var FilesChooser = library.uploads.FilesChooser;

var html = __module__.html;



module.exports = Controller.create(Dashboard, {
  __body__: function() {
    return {
      content: html({})
    };
  },

  __ready__: function() {
    this.saveSet('Untitled', '1.0', function() {
      navigation.navigate('/screenshots/dashboard/');
    });

    return;

    // TODO(Taylor): Remove all this stuff.
    var form = dom.get('#name-app-form');

    this.bind(form, 'submit', this.onSubmitForm, this);

    form.get('input[type=text]').element.focus();
  },

  onSubmitForm: function(evt) {
    evt.preventDefault();

    var values = evt.target.serializeForm();
    var $toDisable = evt.target.find('input');
    iter.forEach($toDisable, function($d) { $d.disable(); });
    this.saveSet(values['name'], values['version'], function() {
      iter.forEach($toDisable, function($d) { $d.enable(); });
    });
  },

  saveSet: function(name, version, onError) {
    var platform = window.sessionStorage['platform'];
    LKAPIClient.addScreenshotSet(name, version, platform, {
      onSuccess: function(set) {
        this.maybeSaveFirstShot(set, function() {
          navigation.navigate('/screenshots/dashboard/' + set['id']);
        }, this);
      },
      onError: function() {
        onError();
      },
      context: this
    });
  },

  maybeSaveFirstShot: function(set, cb, context) {
    var screenshotId = window.sessionStorage['screenshot-id'];
    var backgroundImageId = window.sessionStorage['background-image-id'];
    if (!screenshotId) {
      cb.call(context);
      return;
    }

    var params = JSON.parse(window.sessionStorage['screenshot-config'] || '{}');

    // TODO(Taylor): Stop duplicating this.
    delete window.sessionStorage['screenshot-id'];
    delete window.sessionStorage['screenshot-url'];
    delete window.sessionStorage['background-image-id'];
    delete window.sessionStorage['background-image-url'];
    delete window.sessionStorage['screenshot-config'];

    params['screenshot_image_id'] = screenshotId;
    params['background_image_id'] = backgroundImageId;

    LKAPIClient.addShot(set['id'], params, {
      onComplete: function() {
        cb.call(context);
      },
      context: this
    });
  }
});
