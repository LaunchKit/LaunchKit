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

var navigation = skit.platform.navigation;


module.exports = {
  isMobile: function() {
    var ua = navigation.userAgent() || '';
    return !!ua.match(/\b(iPad|iPhone|iPod|Android)\b/);
  },

  findCompatibleMobilePlatform: function() {
    var ua = navigation.userAgent() || '';
    var iOS = ua.match(/\b(iPad|iPhone|iPod)\b/);
    if (iOS) {
      if (iOS[1] == 'iPad') {
        return 'ipad';
      }
      return 'iphone';
    }

    var androidVersion = ua.match(/Android +([0-9\.]*)/);
    if (androidVersion && androidVersion[1].match(/^[4-9]/)) {
      return 'android';
    }

    return null;
  }
};
