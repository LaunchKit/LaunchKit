'use strict';
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

var events = skit.browser.events;
var iter = skit.platform.iter;
var navigation = skit.platform.navigation;
var util = skit.platform.util;

var LKAPIClient = library.api.LKAPIClient;
var TitledOverlay = library.overlays.TitledOverlay;

var html = __module__.html;

var COPY_APPENDAGE = ' - copy';


var DuplicateSetOverlay = function(set) {
  var newName = set['name'] || '';
  if (newName.indexOf(COPY_APPENDAGE) < 0) {
    newName += COPY_APPENDAGE;
  }

  TitledOverlay.call(this, '', {
    content: html({
      name: newName,
      version: set['version'],
      platform: set['platform']
    })
  });

  this.set = set;

  events.bind(this.getContentContainer().get('form'), 'submit', this.onSubmitForm, this);
};
util.inherits(DuplicateSetOverlay, TitledOverlay);


DuplicateSetOverlay.prototype.onSubmitForm = function(evt) {
  evt.preventDefault();

  var $form = evt.target;
  var form = $form.serializeForm();

  iter.forEach($form.find('input, button, textarea'), function($e) {
    $e.disable();
  });

  LKAPIClient.duplicateScreenshotSet(this.set['id'], form['name'], form['version'], form['platform'], {
    onSuccess: function(newSet) {
      navigation.navigate('/screenshots/dashboard/' + newSet['id']);
    },
    onError: function() {
      iter.forEach($form.find('input, button, textarea'), function($e) {
        $e.enable();
      });
    }
  });
};


module.exports = DuplicateSetOverlay;
