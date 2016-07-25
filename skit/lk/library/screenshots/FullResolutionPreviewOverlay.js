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
var util = skit.platform.util;

var TitledOverlay = library.overlays.TitledOverlay;


var FullResolutionPreviewOverlay = function(canvasWrapper) {
  this.$content = ElementWrapper.fromHtml('<div></div>');
  var img = ElementWrapper.fromHtml('<img src="/__static__/images/pixel.gif" class="screenshot shadowed-box">');
  this.$content.append(img);

  var imgEl = img.element;
  imgEl.style.width = canvasWrapper.phone[canvasWrapper.orientation].naturalWidth;
  imgEl.style.paddingTop = (canvasWrapper.phone[canvasWrapper.orientation].naturalHeight / canvasWrapper.phone[canvasWrapper.orientation].naturalWidth) * 100 + '%';

  setTimeout(function() {
    img.element.src = canvasWrapper.renderToDataURL(1.0);
    imgEl.style.paddingTop = '0';
  }, 250);

  TitledOverlay.call(this, 'Full Resolution Preview', {content: this.$content, className: 'full-resolution-preview-overlay'});
};
util.inherits(FullResolutionPreviewOverlay, TitledOverlay);


module.exports = FullResolutionPreviewOverlay;
