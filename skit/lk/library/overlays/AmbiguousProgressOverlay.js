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

var util = skit.platform.util;
var ElementWrapper = skit.browser.ElementWrapper;

var Overlay = library.overlays.Overlay;

var html = __module__.html;


var AmbiguousProgressOverlay = function(opt_subtext, opt_subsubtext) {
  this.$content = ElementWrapper.fromHtml(html({
    subtext: opt_subtext,
    subsubtext: opt_subsubtext
  }));

  Overlay.call(this, this.$content, {
    backgroundClass: 'progress-overlay-background'
  });

  this.done_ = false;
  this.addShouldDismissListener(function() {
    return this.done_;
  }, this);
};
util.inherits(AmbiguousProgressOverlay, Overlay);


AmbiguousProgressOverlay.prototype.done = function() {
  this.done_ = true;
  Overlay.prototype.hide.call(this);
};


AmbiguousProgressOverlay.prototype.setProgressIsAmbiguous = function() {
  this.$content.removeClass('progressive');
};


AmbiguousProgressOverlay.prototype.setProgressPercent = function(pct) {
  this.$content.addClass('progressive');
  if (!this.bar_) {
    this.bar_ = this.$content.get('.progress-bar-fill');
  }
  this.bar_.element.style.width = pct + '%';
};


AmbiguousProgressOverlay.prototype.setSubtext = function(text) {
  var h3 = this.$content.get('h3');
  h3.setText(text);
  this.position();
};

AmbiguousProgressOverlay.prototype.setSubSubtext = function(text) {
  var p = this.$content.get('p');
  p.setText(text);
  this.position();
};


return AmbiguousProgressOverlay;