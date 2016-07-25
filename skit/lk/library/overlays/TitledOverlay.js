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
var layout = skit.browser.layout;
var util = skit.platform.util;

var Overlay = library.overlays.Overlay;

var html = __module__.html;


function TitledOverlay(title, opt_options) {
  var options = opt_options || {};
  var $container = ElementWrapper.fromHtml(html({
    'title': title,
    'closeButtonTitle': !options.noCloseButton ? (options.closeButtonTitle || 'Close') : null,
    'className': options.className
  }));

  this.$titlebar = $container.get('.titlebar');
  this.$contentContainer = $container.get('.titled-overlay-content');
  if (options.content) {
    this.$contentContainer.append(options.content);
  }

  Overlay.call(this, $container, opt_options);
};
util.inherits(TitledOverlay, Overlay);


TitledOverlay.prototype.getContentContainer = function() {
  return this.$contentContainer;
};


TitledOverlay.prototype.position = function() {
  var outerContent = this.getContent().element;
  outerContent.style.height = 'auto';
  // This should be zero + padding + borders, if any, because
  // everything inside is position: absolute.
  var outerHeight = layout.height(outerContent);
  outerContent.style.height = '';

  var titleBarHeight = layout.height(this.$titlebar);

  var innerContent = this.getContentContainer().element;
  innerContent.style.position = 'static';
  var innerContentHeight = layout.height(innerContent);

  innerContent.style.position = 'absolute';
  innerContent.style.top = titleBarHeight + 'px';

  var totalHeight = innerContentHeight + titleBarHeight + outerHeight;
  outerContent.style.height = Math.min(totalHeight, layout.height(window)) + 'px';

  Overlay.prototype.position.call(this);
};


return TitledOverlay;
