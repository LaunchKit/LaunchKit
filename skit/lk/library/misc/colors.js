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

var string = skit.platform.string;


module.exports = {
  humanInputToHex: function(value, opt_default) {
    value = string.trim(value || '').toUpperCase();
    if (value.substring(0, 1) == '#' && value.length < 7) {
      var r = value.substring(1,2) || '0';
      var g = value.substring(2,3) || '0';
      var b = value.substring(3,4) || '0';
      value = '#' + r + r + g + g + b + b;
    }

    if (!/^#[A-F0-9]{6}$/.test(value)) {
      return opt_default || null;
    }
    return value;
  },

  onlyMidrangeColors: function(rgbArrays) {
    var avgs = [];
    var i;
    for (i = 0; i < rgbArrays.length; i++) {
      var a = rgbArrays[i];
      var avg = ((a[0] + a[1] + a[2]) / 3.0) / 255;
      avgs.push([a, avg]);
    }

    var bright = [];
    for (i = 0; i < avgs.length; i++) {
      if (avgs[i][1] < 0.8 && avgs[i][1] > 0.4) {
        bright.push(avgs[i][0]);
      }
    }

    return bright;
  },

  lightishVersion: function(rgbArray, opt_threshold) {
    rgbArray = rgbArray.slice();

    var threshold = (255 * 3) * (opt_threshold || 0.8);
    var step = 10;
    while (rgbArray[0] + rgbArray[1] + rgbArray[2] < threshold) {
      rgbArray[0] = Math.min(rgbArray[0] + step, 255);
      rgbArray[1] = Math.min(rgbArray[1] + step, 255);
      rgbArray[2] = Math.min(rgbArray[2] + step, 255);
    }
    return rgbArray;
  },
  darkishVersion: function(rgbArray, opt_threshold) {
    rgbArray = rgbArray.slice();

    var threshold = (255 * 3) * (opt_threshold || 0.25);
    var step = 10;
    while (rgbArray[0] + rgbArray[1] + rgbArray[2] > threshold) {
      rgbArray[0] = Math.max(rgbArray[0] - step, 0);
      rgbArray[1] = Math.max(rgbArray[1] - step, 0);
      rgbArray[2] = Math.max(rgbArray[2] - step, 0);
    }
    return rgbArray;
  },

  rgbToHex: function(rgbArray) {
    var bin = rgbArray[0] << 16 | rgbArray[1] << 8 | rgbArray[2];
    return '#' + (function(h) {
      return new Array(7 - h.length).join("0") + h
    })(bin.toString(16).toUpperCase());
  }
};
