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

var layout = skit.browser.layout;


var module = {
  sizeInWindow: function(aspectRatio, opt_options) {
    var options = opt_options || {};

    var windowWidth = layout.width(window);
    var windowHeight = layout.height(window);

    var boxSize = options.targetSize || 0.85;
    if (windowWidth <= 640) {
      boxSize = options.targetSizeTouch;
    }

    if (options.horizontalPadding) {
      windowWidth -= options.horizontalPadding;
    }

    var boxHeight = windowHeight * boxSize;
    var boxWidth = windowWidth * boxSize;

    return module.sizeInBox(aspectRatio, boxWidth, boxHeight);
  },

  aspectFit: function(imageWidth, imageHeight, boxWidth, boxHeight) {
    var width, height;

    var aspectRatio = imageWidth / imageHeight;
    if (aspectRatio > 1) {
      // wide
      width = boxWidth;
      height = width / aspectRatio;

      if (height < boxHeight) {
        height = boxHeight;
        width = height * aspectRatio;
      }

    } else {
      // tall
      height = boxHeight;
      width = height * aspectRatio;

      if (width < boxWidth) {
        width = boxWidth;
        height = width / aspectRatio;
      }
    }

    return {width: width, height: height};
  },

  sizeInBox: function(aspectRatio, boxWidth, boxHeight) {
    var width, height;
    if (aspectRatio > 1) {
      // wide
      width = boxWidth;
      height = width / aspectRatio;

      if (height > boxHeight) {
        height = boxHeight;
        width = height * aspectRatio;
      }

    } else {
      // tall
      height = boxHeight;
      width = height * aspectRatio;

      if (width > boxWidth) {
        width = boxWidth;
        height = width / aspectRatio;
      }
    }

    return {width: width, height: height};
  }
};

return module;