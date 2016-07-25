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
var dom = skit.browser.dom;
var events = skit.browser.events;
var layout = skit.browser.layout;
var iter = skit.platform.iter;
var util = skit.platform.util;


var OVERLAYS_STACK = [];

var OVERLAY_ANIMATION_DURATION = 200;

var KEY_CODE_ESCAPE = 27;


var Overlay = function($content, opt_options) {
  this.options = opt_options || {};

  if ('hasBackground' in this.options) {
    this.hasBackground = !!this.options.hasBackground;
  } else {
    this.hasBackground = true;
  }

  this.$overlayContent_ = $content;
  this.$overlayContent_.addClass('overlay');

  if (this.options.positionAnchor) {
    this.$overlayContent_.addClass('absolute');
  } else {
    this.$overlayContent_.addClass('fixed');
  }

  this.shouldDismissListeners_ = [];
  this.didDismissListeners_ = [];

  // Setup close behavior.
  events.delegate(this.$overlayContent_, '.close-overlay', 'click', this.onClickHide_, this);
};


Overlay.Position = {
  ABOVE_LEFT: 'al',
  ABOVE_RIGHT: 'ar',
  ABOVE_CENTER: 'ac',
  BELOW_LEFT: 'bl',
  BELOW_RIGHT: 'br',
  BELOW_CENTER: 'bc'
};


Overlay.prototype.getContent = function() {
  return this.$overlayContent_;
};


Overlay.prototype.addShouldDismissListener = function(fn, opt_context) {
  this.shouldDismissListeners_.push([fn, opt_context]);
};


Overlay.prototype.addDidDismissListener = function(fn, opt_context) {
  this.didDismissListeners_.push([fn, opt_context]);
};


Overlay.prototype.onClickHide_ = function(e) {
  this.hide();
};


Overlay.prototype.onClickBackground_ = function(e) {
  if (e.target.up('.overlay')) {
    return;
  }

  this.hide();
};


Overlay.prototype.beforeShow = function() {
  // Overrideable.
  this.keyUpListener_ = events.bind(window, 'keyup', this.onDocumentKeyUp_, this);
};


Overlay.prototype.afterShow = function() {
  // In the very weird, why-am-I-handling-it-here case of opening modals
  // from iframes, this line of code sends focus back to the current window
  // and should otherwise have no effect on anything, until of course this
  // comment is read by an angry engineer (probably me) in a few months
  // or years.
  window.focus();
};


Overlay.prototype.show = function() {
  if (this.shown_) {
    return;
  }
  this.shown_ = true;

  OVERLAYS_STACK.push(this);

  this.beforeShow();

  if (this.hasBackground) {
    this.$background = ElementWrapper.fromHtml('<div class="overlay-background"></div>');
    if (this.options.backgroundClass) {
      this.$background.addClass(this.options.backgroundClass);
    }
    this.$background.appendTo(document.body);
  }

  this.$overlayContent_.originalParent_ = this.$overlayContent_.parent();

  this.$overlayContent_.appendTo(document.body);

  this.position();
  this.resizeListener_ = events.bind(window, 'resize', this.position, this);

  util.nextTick(function() {
    this.position();

    // Set up the listeners on the next tick so we don't catch any
    // currently-happening events.
    this.clickHideListener_ = events.bind(this.$background || document,
        'click', this.onClickBackground_, this);

    this.$overlayContent_.addClass('active');
    if (this.$background) {
      this.$background.addClass('active');
    }

    this.afterShow();
  }, this);
};


Overlay.prototype.beforeHide = function() {
  // Overrideable.
  events.unbind(this.keyUpListener_);
  delete this.keyUpListener_;
};
Overlay.prototype.afterHide = function() {
  // Overrideable.
};


Overlay.prototype.hide = function() {
  var shouldDismiss = true;
  iter.forEach(this.shouldDismissListeners_, function(listenerAndContext) {
    var listener = listenerAndContext[0];
    var context = listenerAndContext[1];
    shouldDismiss = shouldDismiss && listener.call(context, this);
  }, this);

  if (shouldDismiss) {
    this.hide_();

    iter.forEach(this.didDismissListeners_, function(listenerAndContext) {
      var listener = listenerAndContext[0];
      var context = listenerAndContext[1];
      listener.call(context, this);
    });
  }
};


Overlay.prototype.hide_ = function() {
  if (!this.shown_ || this.hiding) {
    return;
  }
  this.hiding = true;

  this.beforeHide();

  this.$overlayContent_.removeClass('active');

  // Clean up the background click listeners.
  if (this.$background) {
    this.$background.removeClass('active');
  }

  events.unbind(this.clickHideListener_);
  delete this.clickHideListener_;
  events.unbind(this.resizeListener_);
  delete this.resizeListener_;

  util.setTimeout(function() {
    this.remove_();
    this.shown_ = false;
    this.hiding = false;

    this.afterHide();

    OVERLAYS_STACK = iter.filter(OVERLAYS_STACK, function(item) {
      return item !== this;
    }, this);
  }, OVERLAY_ANIMATION_DURATION, this);
};


Overlay.prototype.isShown = function() {
  return this.shown_;
};


Overlay.prototype.remove_ = function() {
  if (this.$background) {
    this.$background.remove();
    this.$background = null;
  }

  var $parent = this.$overlayContent_.originalParent_;
  delete this.$overlayContent_.originalParent_;

  this.$overlayContent_.remove();
  if ($parent) {
    this.$overlayContent_.appendTo($parent);
  }
};


Overlay.prototype.position = function(opt_evt) {
  if (this.options.positionAnchor) {
    this.positionRelativeTo_(this.options.positionAnchor, this.options.overlayPosition,
        this.options.arrowWidth, this.options.arrowHeight)
  } else if (!this.options.manuallyPositioned) {
    this.positionCentered_();
  }
};


Overlay.prototype.positionRelativeTo_ = function(target, overlayPosition,
    opt_arrowWidth, opt_arrowHeight) {

  var anchorPosition = layout.position(target);
  var offsetParent = layout.offsetParent(target);

  var el = (target.element || target).parentNode;
  while (offsetParent) {
    // Adjust the position to include offsets from scrolling.
    anchorPosition.top += el.scrollTop;
    anchorPosition.left += el.scrollLeft;

    if (el == offsetParent) {
      break;
    }
    el = el.parentNode;
  }

  var anchorWidth = layout.width(target);
  var anchorHeight = layout.height(target);

  var myTop = anchorPosition.top;
  var myLeft = anchorPosition.left + anchorWidth / 2.0;

  var overlayWidth = layout.width(this.$overlayContent_);
  var overlayHeight = layout.height(this.$overlayContent_);

  var arrowWidth = isNaN(+opt_arrowWidth) ? 20 : +opt_arrowWidth;
  var arrowHeight = isNaN(+opt_arrowHeight) ? 5 : +opt_arrowHeight;

  switch (overlayPosition) {
    case Overlay.Position.ABOVE_CENTER:
    case Overlay.Position.ABOVE_LEFT:
    case Overlay.Position.ABOVE_RIGHT:
      myTop -= overlayHeight - arrowHeight;
      break;
    case Overlay.Position.BELOW_LEFT:
    case Overlay.Position.BELOW_RIGHT:
    case Overlay.Position.BELOW_CENTER:
    default:
      myTop += anchorHeight + arrowHeight;
      break;
  }

  switch (overlayPosition) {
    case Overlay.Position.ABOVE_LEFT:
    case Overlay.Position.BELOW_LEFT:
      myLeft -= overlayWidth;
      myLeft += arrowWidth;
      break;
    case Overlay.Position.ABOVE_RIGHT:
    case Overlay.Position.BELOW_RIGHT:
      myLeft -= arrowWidth;
      break;
    case Overlay.Position.ABOVE_CENTER:
    case Overlay.Position.BELOW_CENTER:
    default:
      myLeft -= overlayWidth / 2.0;
      break;
  }

  var content = this.$overlayContent_.element;
  content.style.left = myLeft + 'px';
  content.style.top = myTop + 'px';
};


Overlay.prototype.positionCentered_ = function() {
  var windowWidth = layout.width(window);
  var windowHeight = layout.height(window);

  var overlayWidth = layout.width(this.$overlayContent_);
  var overlayHeight = layout.height(this.$overlayContent_);

  var myLeft = (windowWidth / 2.0) - (overlayWidth / 2.0);
  var myTop = (windowHeight / 2.0) - (overlayHeight / 2.0);

  var content = this.$overlayContent_.element;
  content.style.left = myLeft + 'px';
  content.style.top = myTop + 'px';
};


Overlay.prototype.onDocumentKeyUp_ = function(e) {
  switch (e.keyCode) {
    case KEY_CODE_ESCAPE:
      if (OVERLAYS_STACK[OVERLAYS_STACK.length - 1] === this) {
        e.preventDefault();
        this.hide();
      }
      break;
  }
};


return Overlay;
