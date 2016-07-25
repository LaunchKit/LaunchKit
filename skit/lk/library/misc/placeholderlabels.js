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
var events = skit.browser.events;
var iter = skit.platform.iter;
var string = skit.platform.string;


var togglePlaceholderHasContent_ = function($container, opt_evt) {
  var value = $container.get('input').value();
  var hasValue = !!string.trim(value);
  if (!hasValue && opt_evt) {
    var code = opt_evt.metaKey ? -1 : opt_evt.keyCode;
    if (code >= 48 && code <= 90) {
      hasValue = true;
    }
  }

  if (hasValue) {
    $container.addClass('has-content');
  } else {
    $container.removeClass('has-content');
  }
};


var init = function(opt_parent) {
  var $parent = opt_parent || new ElementWrapper(document.body);
  var $labels = $parent.find('.placeholder-label');

  iter.forEach($labels, function($container) {
    togglePlaceholderHasContent_($container);

    var $label = $container.get('label');
    events.bind($label, 'click', function(e) {
      e.preventDefault();

      var input = $container.get('input');
      input.element.focus();
      input.element.select();
    });

    events.bind($container, 'keydown', function(e) {
      togglePlaceholderHasContent_($container, e);
    });
    events.bind($container, 'keyup', function(e) {
      // Don't send the event here because the value is done being modified.
      togglePlaceholderHasContent_($container);
    });

    $container.addClass('ready');
  });
};


return {
  'init': init
};
