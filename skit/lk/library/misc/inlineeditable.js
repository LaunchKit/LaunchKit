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

var PubSub = skit.platform.PubSub;
var iter = skit.platform.iter;
var util = skit.platform.util;
var ElementWrapper = skit.browser.ElementWrapper;
var events = skit.browser.events;
var layout = skit.browser.layout;


var EDITABLE_SHOULD_COMMIT = 'editable-should-commit';
var EDITABLE_WILL_COMMIT = 'editable-will-commit';
var EDITABLE_DID_COMMIT = 'editable-did-commit';
var KEY_CODE_ENTER = 13;
var KEY_CODE_ESCAPE = 27;

var Editable = function($container) {
  this.$container_ = $container;
  this.editing_ = false;

  events.bind($container, 'click', this.onClick_, this);
  events.bind($container, 'keydown', this.onKeyDown_, this);
};

Editable.prototype.onClick_ = function(e) {
  if (this.editing_) {
    var input = this.$container_.get('input').element;
    input.focus();
  } else {
    this.startEditing_();
  }
};

Editable.prototype.onKeyDown_ = function(e) {
  if (e.keyCode == KEY_CODE_ESCAPE) {
    e.stopPropagation();
    this.stopEditing_();
    return;
  }

  var shouldCommit = e.keyCode == KEY_CODE_ENTER;
  var doCommit = function() {
    shouldCommit = true;
  };
  PubSub.sharedPubSub().publish(EDITABLE_SHOULD_COMMIT, this.$container_.element, e, doCommit);

  if (!shouldCommit) {
    return;
  }

  // Enter was pressed. Prevent IE8 from "submitting" the "form".
  e.preventDefault();

  this.save_();
};

Editable.prototype.onBlur_ = function(e) {
  // By default, don't commit when blurring.
  var shouldCommit = false;
  var doCommit = function() {
    shouldCommit = true;
  };
  PubSub.sharedPubSub().publish(EDITABLE_SHOULD_COMMIT, this.$container_.element, e, doCommit);

  // If we replace the input in this handler, we get an error
  // because we've modified the element while handling an event for it.
  if (shouldCommit) {
    util.nextTick(this.save_, this);
  } else {
    util.nextTick(this.stopEditing_, this);
  }
};

Editable.prototype.save_ = function() {
  if (!this.editing_) {
    return;
  }
  var $input = this.$container_.get('input');
  var newText = $input.value();

  var isCanceled = false;
  var cancel = function() {
    isCanceled = true;
  };
  PubSub.sharedPubSub().publish(EDITABLE_WILL_COMMIT, this.$container_.element, newText, cancel);

  if (isCanceled) {
    // Cancel out if any of the listeners decided our new text was no good.
    return;
  }

  this.text_ = newText;
  this.stopEditing_();

  PubSub.sharedPubSub().publish(EDITABLE_DID_COMMIT, this.$container_.element, newText);
};

Editable.prototype.startEditing_ = function() {
  this.$container_.addClass('editing');
  this.editing_ = true;
  this.text_ = this.$container_.getText();

  var width = layout.width(this.$container_);
  var input = document.createElement('input');
  input.type = 'text';
  input.value = this.text_;

  input.style.width = width + 'px';
  this.$container_.element.style.width = width + 'px';

  this.$container_.replaceChildren(input);

  this.blurListener_ = events.bind(input, 'blur', this.onBlur_, this);

  util.nextTick(function() {
    input.focus();
    input.select();
  });
};

Editable.prototype.stopEditing_ = function() {
  this.$container_.setText(this.text_);
  this.editing_ = false;

  this.$container_.removeClass('editing');
  this.$container_.element.style.width = '';

  events.unbind(this.blurListener_);
};


var initSelector = function($editables) {
  iter.forEach($editables, function($editable) {
    if ($editable.getData('initialized')) {
      return;
    }

    new Editable($editable);

    $editable.setData('initialized', '1');
  });
};

var init = function(opt_parent) {
  var $parent = opt_parent || new ElementWrapper(document.body);
  var $editable = $parent.find('.inline-editable');

  initSelector($editable);
};


module.exports = {
  EDITABLE_SHOULD_COMMIT: EDITABLE_SHOULD_COMMIT,
  EDITABLE_WILL_COMMIT: EDITABLE_WILL_COMMIT,
  EDITABLE_DID_COMMIT: EDITABLE_DID_COMMIT,
  init: init
};
