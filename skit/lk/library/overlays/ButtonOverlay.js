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

var ElementWrapper = skit.browser.ElementWrapper;
var events = skit.browser.events;
var iter = skit.platform.iter;
var string = skit.platform.string;
var util = skit.platform.util;

var Overlay = library.overlays.Overlay;


var ButtonOverlay = function(headerText, opt_subtext, opt_firstButton) {
  this.$content = ElementWrapper.fromHtml('<div class="button-overlay webapp"></div>');

  this.$header = ElementWrapper.fromHtml('<h3/>');
  this.$header.setText(headerText);

  this.$content.append(this.$header);
  if (opt_subtext) {
    var subtextArray;
    if (typeof opt_subtext == 'string') {
      subtextArray = [opt_subtext];
    } else {
      subtextArray = opt_subtext;
    }
    iter.forEach(subtextArray, function(subtext) {
      subtext = string.escapeHtml(subtext);
      subtext = subtext.replace(/\*\*(.+?)\*\*/g, function(_, match) {
        return '<strong>' + match + '</strong>';
      });
      var $subtext = ElementWrapper.fromHtml('<p/>');
      $subtext.element.innerHTML = subtext;
      this.$content.append($subtext);
    }, this);
  }

  events.delegate(this.$content, '.btn', 'click', this.onClickButton_, this);

  Overlay.call(this, this.$content, {
    backgroundClass: 'button-overlay-background'
  });

  this.buttonCount_ = 0;
  this.cancelable_ = true;
  this.listenerByIndex_ = {};

  this.addShouldDismissListener(this.shouldDismiss_, this);

  if (opt_firstButton) {
    this.addButton(opt_firstButton);
  }
};
util.inherits(ButtonOverlay, Overlay);


ButtonOverlay.prototype.setCancelable = function(cancelable) {
  this.cancelable_ = cancelable;
};


ButtonOverlay.prototype.afterShow = function() {
  Overlay.prototype.afterShow.call(this);

  var button =this.$content.get('.btn');
  if (button) {
    button.element.focus();
  }
};


ButtonOverlay.prototype.addButton = function(name, opt_listener, opt_context) {
  var index = this.buttonCount_++;

  var $button = ElementWrapper.fromHtml('<button class="btn btn-block"></button>');
  $button.setText(name);
  $button.setData('index', index);

  if (index == 0) {
    $button.addClass('btn-primary');
  }
  this.$content.append($button);

  if (opt_listener) {
    this.listenerByIndex_[index] = [opt_listener, opt_context];
  }
};


ButtonOverlay.prototype.addLinkButton = function(name, href, opt_attrs, opt_listener, opt_context) {
  var index = this.buttonCount_++;

  var $link = ElementWrapper.fromHtml('<a class="btn btn-block"></a>');
  $link.setText(name);
  $link.setData('index', index);
  $link.element.setAttribute('href', href);
  if (opt_attrs) {
    for (var k in opt_attrs) {
      $link.element.setAttribute(k, opt_attrs[k]);
    }
  }

  if (index == 0) {
    $link.addClass('btn-primary');
  }
  this.$content.append($link);

  if (opt_listener) {
    this.listenerByIndex_[index] = [opt_listener, opt_context];
  }
};


ButtonOverlay.prototype.getButtonCount = function() {
  return this.buttonCount_;
};


ButtonOverlay.prototype.setPrimaryButtonIndex = function(index) {
  var $buttons = this.$content.find('button, .button');
  iter.forEach($buttons, function($button) {
    $button.removeClass('btn-primary');
  });

  if (index > -1) {
    $buttons[i].addClass('btn-primary');
  }
};


ButtonOverlay.prototype.setButtonDangerous = function(index) {
  var $buttons = this.$content.find('button, .button');
  $buttons[index].removeClass('btn-primary');
  $buttons[index].addClass('btn-danger');
};


ButtonOverlay.prototype.onClickButton_ = function(e) {
  if (!e.target.matches('a')) {
    e.preventDefault();
  }

  var $button = e.currentTarget;
  var index = +($button.getData('index'));

  this.hasSelected_ = true;
  this.selectedIndex = index;

  var listenerAndContext = this.listenerByIndex_[index];
  if (listenerAndContext) {
    listenerAndContext[0].call(listenerAndContext[1], this);
    delete this.listenerByIndex_[index];
  }

  this.hide();
};


ButtonOverlay.prototype.shouldDismiss_ = function() {
  return this.cancelable_ || this.hasSelected_;
};


return ButtonOverlay;
