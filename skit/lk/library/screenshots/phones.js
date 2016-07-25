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

var events = skit.browser.events;
var iter = skit.platform.iter;
var util = skit.platform.util;

var ScreenshotCanvasWrapper = library.screenshots.ScreenshotCanvasWrapper;


var IPHONE_4 = 'iphone4';
var IPHONE_5 = 'iphone5';
var IPHONE_6 = 'iphone6';
var IPHONE_6PLUS = 'iphone6plus';
var IPAD = 'ipad';
var IPAD_LANDSCAPE = 'ipadlandscape';
var IPADPRO = 'ipadpro';
var IPADPRO_LANDSCAPE = 'ipadprolandscape';

var NEXUS_5X = 'nexus5x';
var NEXUS_6P = 'nexus6p';
var NEXUS_9 = 'nexus9';
var NEXUS_9_LANDSCAPE = 'nexus9landscape';

var IPHONES = [{
  name: IPHONE_4,
  requiresPremium: true,
  properName: 'iPhone 4 & 4s',
  filenamePrefix: '3.5-inch (iPhone 4)',
  overrideName: 'iphone480',

  portrait: {
    width: 320,
    height: 480,
    screenLeft: 78 / 636,
    screenTop: 232 / 1192,
    screenWidth: 484 / 636,
    screenHeight: 728 / 1192
  },
  landscape: {},

  naturalMultiplier: 2,

  white: '/__static__/devices/iPhone4White.png',
  black: '/__static__/devices/iPhone4Black.png',
  gold: '/__static__/devices/iPhone4White.png',
  rose: '/__static__/devices/iPhone4White.png'
}, {
  name: IPHONE_5,
  requiresPremium: true,
  properName: 'iPhone 5 & 5s',
  filenamePrefix: '4-inch (iPhone 5)',
  overrideName: 'iphone568',

  portrait: {
    width: 320,
    height: 568,
    screenLeft: 79 / 637,
    screenTop: 211 / 1271,
    screenWidth: 485 / 637,
    screenHeight: 861 / 1271
  },
  landscape: {},

  naturalMultiplier: 2,
  white: '/__static__/devices/iPhone5sWhite.png',
  black: '/__static__/devices/iPhone5sBlack.png',
  gold: '/__static__/devices/iPhone5sGold.png',
  rose: '/__static__/devices/iPhone5sWhite.png'
}, {
  name: IPHONE_6,
  requiresPremium: true,
  properName: 'iPhone 6 & 6s',
  filenamePrefix: '4.7-inch (iPhone 6)',
  overrideName: 'iphone667',

  portrait: {
    width: 375,
    height: 667,
    screenLeft: 77 / 735,
    screenTop: 207 / 1437,
    screenWidth: 581 / 735,
    screenHeight: 1034 / 1437
  },
  landscape: {},

  naturalMultiplier: 2,

  white: '/__static__/devices/iPhone6White.png',
  black: '/__static__/devices/iPhone6Black.png',
  gold: '/__static__/devices/iPhone6Gold.png',
  rose: '/__static__/devices/iPhone6Rose.png'
}, {
  name: IPHONE_6PLUS,
  properName: 'iPhone 6 Plus & 6s Plus',
  filenamePrefix: '5.5-inch (iPhone 6+)',
  overrideName: 'iphone736',

  portrait: {
    width: 414,
    height: 736,
    screenLeft: 106 / 1151,
    screenTop: 315 / 2285,
    screenWidth: 940 / 1151,
    screenHeight: 1669 / 2285
  },
  landscape: {},

  naturalMultiplier: 3,

  white: '/__static__/devices/iPhone6PlusWhite.png',
  black: '/__static__/devices/iPhone6PlusBlack.png',
  gold: '/__static__/devices/iPhone6PlusGold.png',
  rose: '/__static__/devices/iPhone6PlusRose.png'
}, {
  name: IPAD,
  requiresPremium: true,
  properName: 'iPad',
  filenamePrefix: 'iPad',
  overrideName: 'ipad2151',

  portrait: {
    width: 1536,
    height: 2048,
    screenLeft: 128 / 1549,
    screenTop: 217 / 2160,
    screenWidth: 1294 / 1549,
    screenHeight: 1726 / 2160
  },
  landscape: {
    width: 2048,
    height: 1536,
    screenLeft: 218 / 2160,
    screenTop: 126 / 1548,
    screenWidth: 1725 / 2160,
    screenHeight: 1294 / 1548
  },

  deviceSizeMultiplier: 1,
  naturalMultiplier: 1,
  isIPad: true,

  white: '/__static__/devices/iPadWhite.png',
  black: '/__static__/devices/iPadBlack.png',
  gold: '/__static__/devices/iPadGold.png',
  rose: '/__static__/devices/iPadWhite.png',
  whiteLandscape: '/__static__/devices/iPadWhiteLandscape.png',
  blackLandscape: '/__static__/devices/iPadBlackLandscape.png',
  goldLandscape: '/__static__/devices/iPadGoldLandscape.png',
  roseLandscape: '/__static__/devices/iPadWhiteLandscape.png'
}, {
  name: IPADPRO,
  requiresPremium: true,
  properName: 'iPad Pro',
  filenamePrefix: 'iPad Pro',
  overrideName: 'ipad2151',

  portrait: {
    width: 2048,
    height: 2732,
    screenLeft: 134 / 2108,
    screenTop: 235 / 2924,
    screenWidth: 1840 / 2108,
    screenHeight: 2455 / 2924
  },
  landscape: {
    width: 2732,
    height: 2048,
    screenLeft: 235 / 2924,
    screenTop: 134 / 2108,
    screenWidth: 2455 / 2924,
    screenHeight: 1840 / 2108
  },

  deviceSizeMultiplier: 1,
  naturalMultiplier: 1,
  isIPad: true,

  white: '/__static__/devices/iPadProWhite.png',
  black: '/__static__/devices/iPadProBlack.png',
  gold: '/__static__/devices/iPadProGold.png',
  rose: '/__static__/devices/iPadProWhite.png',
  whiteLandscape: '/__static__/devices/iPadProWhiteLandscape.png',
  blackLandscape: '/__static__/devices/iPadProBlackLandscape.png',
  goldLandscape: '/__static__/devices/iPadProGoldLandscape.png',
  roseLandscape: '/__static__/devices/iPadProWhiteLandscape.png'
} ,{
  name: NEXUS_5X,
  properName: 'Nexus 5x',
  filenamePrefix: 'Nexus 5x',
  overrideName: 'nexus5x',

  portrait: {
    width: 1080,
    height: 1920,
    screenLeft: 83 / 1255,
    screenTop: 261 / 2466,
    screenWidth: 1080 / 1255,
    screenHeight: 1920 / 2466
  },
  landscape: {},

  naturalMultiplier: 1,

  black: '/__static__/devices/Nexus5xBlack.png',
  white: '/__static__/devices/Nexus5xBlack.png',
  gold: '/__static__/devices/Nexus5xBlack.png',
  rose: '/__static__/devices/Nexus5xBlack.png'
} ,{
  name: NEXUS_6P,
  properName: 'Nexus 6P',
  filenamePrefix: 'Nexus 6P',
  overrideName: 'nexus6p',

  portrait: {
    width: 1440,
    height: 2560,
    screenLeft: 118 / 1684,
    screenTop: 388 / 3272,
    screenWidth: 1440 / 1684,
    screenHeight: 2560 / 3272
  },
  landscape: {},

  naturalMultiplier: 1,

  black: '/__static__/devices/Nexus6PBlack.png',
  white: '/__static__/devices/Nexus6PBlack.png',
  gold: '/__static__/devices/Nexus6PBlack.png',
  rose: '/__static__/devices/Nexus6PBlack.png'
}, {
  name: NEXUS_9,
  requiresPremium: true,
  properName: 'Nexus 9',
  filenamePrefix: 'Nexus 9',
  overrideName: 'nexus9',

  portrait: {
    width: 1536,
    height: 2048,
    screenLeft: 156 / 1847,
    screenTop: 320 / 2686,
    screenWidth: 1536 / 1847,
    screenHeight: 2048 / 2686
  },
  landscape: {
    width: 2048,
    height: 1536,
    screenLeft: 320 / 2686,
    screenTop: 156 / 1847,
    screenWidth: 2048 / 2686,
    screenHeight: 1536 / 1847
  },

  deviceSizeMultiplier: 1,
  naturalMultiplier: 1,
  isIPad: true,

  white: '/__static__/devices/Nexus9Black.png',
  black: '/__static__/devices/Nexus9Black.png',
  gold: '/__static__/devices/Nexus9Black.png',
  rose: '/__static__/devices/Nexus9Black.png',
  whiteLandscape: '/__static__/devices/Nexus9BlackLandscape.png',
  blackLandscape: '/__static__/devices/Nexus9BlackLandscape.png',
  goldLandscape: '/__static__/devices/Nexus9BlackLandscape.png',
  roseLandscape: '/__static__/devices/Nexus9BlackLandscape.png'
}
].reverse(); // reverse to show newest phones first

var IPHONES_BY_NAME = {};
iter.forEach(IPHONES, function(phone, i) {
  IPHONES_BY_NAME[phone.name] = phone;
  phone.naturalWidth = phone.naturalMultiplier * phone.portrait.width;
  phone.naturalHeight = phone.naturalMultiplier * phone.portrait.height;
  phone.portrait.naturalWidth = phone.naturalWidth;
  phone.portrait.naturalHeight = phone.naturalHeight;
  phone.landscape.naturalWidth = phone.naturalHeight;
  phone.landscape.naturalHeight = phone.naturalWidth;
  phone.resolution = phone.naturalWidth+'x'+phone.naturalHeight;
  phone.index = i;
});

PHONE_OVERRIDES = [];
iter.forEach(IPHONES, function(p){
  if (!p.isIPad) {
    PHONE_OVERRIDES.push({
      deviceType: p.overrideName,
      properName: p.properName,
      deviceName: p.name,
      resolution: p.resolution
    });
  }
})
TABLET_OVERRIDES = [{
  deviceType:IPHONES_BY_NAME[IPADPRO].overrideName,
  properName:IPHONES_BY_NAME[IPADPRO].properName,
  deviceName:IPHONES_BY_NAME[IPADPRO].name,
  resolution:IPHONES_BY_NAME[IPADPRO].resolution
}];

// Is screenshot?

function roundAspect(ratio) {
  return (Math.round(ratio * 1000) / 1000.0);
}

var SCREENSHOT_SIZES = [[320, 568], [320, 480], [1536, 2048], [2048, 1536]];
var ASPECT_RATIOS = [];
iter.forEach(SCREENSHOT_SIZES, function(sz) {
  ASPECT_RATIOS.push(roundAspect(sz[0] / sz[1]));
  // This accommodates the case where the status bar has been removed.
  ASPECT_RATIOS.push(roundAspect(sz[0] / (sz[1] - 20)));
});

function isScreenshot(img) {
  var rounded = roundAspect(img.width / img.height);
  return !!iter.find(ASPECT_RATIOS, function(ratio) {
    return Math.abs(rounded - ratio) <= 0.01;
  });
}

module.exports = {
  IPHONES: IPHONES,
  IPHONES_BY_NAME: IPHONES_BY_NAME,

  IPHONE_4: IPHONE_4,
  IPHONE_5: IPHONE_5,
  IPHONE_6: IPHONE_6,
  IPHONE_6PLUS: IPHONE_6PLUS,
  IPAD: IPAD,
  IPAD_LANDSCAPE : IPAD_LANDSCAPE,
  IPADPRO: IPADPRO,
  IPADPRO_LANDSCAPE : IPADPRO_LANDSCAPE,

  NEXUS_5X: NEXUS_5X,
  NEXUS_6P: NEXUS_6P,
  NEXUS_9: NEXUS_9,
  NEXUS_9_LANDSCAPE: NEXUS_9_LANDSCAPE,

  screenshotCanvasWrappersInContainer: function($container) {
    var $phones = $container.find('.screenshot-canvas-container');
    return iter.map($phones, function($phone) {
      var phone = IPHONES_BY_NAME[$phone.getData('name')];
      return new ScreenshotCanvasWrapper(phone, $phone);
    });
  },

  isScreenshot: isScreenshot,
  overrides: {
    phones : PHONE_OVERRIDES,
    tablets : TABLET_OVERRIDES
  }
};