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
var NEXUS_7 = 'nexus7';
var NEXUS_7_LANDSCAPE = 'nexus7landscape';
var NEXUS_9 = 'nexus9';
var NEXUS_9_LANDSCAPE = 'nexus9landscape';

var IOS = [{
  name: IPHONE_4,
  properName: 'iPhone 4s',
  filenamePrefix: '3.5-inch (iPhone 4)',
  type: 'phone',
  overrideName: 'iphone480',
  requiresPremium: true,

  naturalMultiplier: 2,

  portrait: {
    width: 320,
    height: 480,
    screenLeft: 78 / 636,
    screenTop: 232 / 1192,
    screenWidth: 484 / 636,
    screenHeight: 728 / 1192,
    white: {src:'/__static__/devices/iPhone4White.png'},
    black: {src:'/__static__/devices/iPhone4Black.png'},
    gold: {src:'/__static__/devices/iPhone4White.png'},
    rose: {src:'/__static__/devices/iPhone4White.png'}
  },
  landscape: {
    width: 480,
    height: 320,
    screenLeft: 232 / 1192,
    screenTop: 78 / 636,
    screenWidth: 728 / 1192,
    screenHeight: 484 / 636,
    white: {src:'/__static__/devices/iPhone4WhiteLandscape.png'},
    black: {src:'/__static__/devices/iPhone4BlackLandscape.png'},
    gold: {src:'/__static__/devices/iPhone4WhiteLandscape.png'},
    rose: {src:'/__static__/devices/iPhone4WhiteLandscape.png'}
  }
}, {
  name: IPHONE_5,
  properName: 'iPhone 5s & SE',
  filenamePrefix: '4-inch (iPhone 5)',
  type: 'phone',
  overrideName: 'iphone568',
  requiresPremium: true,

  naturalMultiplier: 2,

  portrait: {
    width: 320,
    height: 568,
    screenLeft: 79 / 637,
    screenTop: 211 / 1271,
    screenWidth: 485 / 637,
    screenHeight: 861 / 1271,
    white: {src:'/__static__/devices/iPhone5sWhite.png'},
    black: {src:'/__static__/devices/iPhone5sBlack.png'},
    gold: {src:'/__static__/devices/iPhone5sGold.png'},
    rose: {src:'/__static__/devices/iPhone5sWhite.png'}
  },
  landscape: {
    width: 568,
    height: 320,
    screenLeft: 211 / 1271,
    screenTop: 79 / 637,
    screenWidth: 861 / 1271,
    screenHeight: 485 / 637,
    white: {src:'/__static__/devices/iPhone5sWhiteLandscape.png'},
    black: {src:'/__static__/devices/iPhone5sBlackLandscape.png'},
    gold: {src:'/__static__/devices/iPhone5sGoldLandscape.png'},
    rose: {src:'/__static__/devices/iPhone5sWhiteLandscape.png'}
  },
}, {
  name: IPHONE_6,
  properName: 'iPhone 6s',
  filenamePrefix: '4.7-inch (iPhone 6)',
  type: 'phone',
  overrideName: 'iphone667',
  requiresPremium: true,

  naturalMultiplier: 2,

  portrait: {
    width: 375,
    height: 667,
    screenLeft: 77 / 735,
    screenTop: 207 / 1437,
    screenWidth: 581 / 735,
    screenHeight: 1034 / 1437,
    white: {src: '/__static__/devices/iPhone6White.png'},
    black: {src: '/__static__/devices/iPhone6Black.png'},
    gold: {src:'/__static__/devices/iPhone6Gold.png'},
    rose: {src:'/__static__/devices/iPhone6Rose.png'}
  },
  landscape: {
    width: 667,
    height: 375,
    screenLeft: 207 / 1437,
    screenTop: 77 / 735,
    screenWidth: 1034 / 1437,
    screenHeight: 581 / 735,
    white: {src: '/__static__/devices/iPhone6WhiteLandscape.png'},
    black: {src: '/__static__/devices/iPhone6BlackLandscape.png'},
    gold: {src: '/__static__/devices/iPhone6GoldLandscape.png'},
    rose: {src: '/__static__/devices/iPhone6RoseLandscape.png'}
  },

}, {
  name: IPHONE_6PLUS,
  properName: 'iPhone 6s Plus',
  filenamePrefix: '5.5-inch (iPhone 6+)',
  type: 'phone',
  overrideName: 'iphone736',

  naturalMultiplier: 3,

  portrait: {
    width: 414,
    height: 736,
    screenLeft: 106 / 1151,
    screenTop: 315 / 2285,
    screenWidth: 940 / 1151,
    screenHeight: 1669 / 2285,
    white: {src:'/__static__/devices/iPhone6PlusWhite.png'},
    black: {src:'/__static__/devices/iPhone6PlusBlack.png'},
    gold: {src:'/__static__/devices/iPhone6PlusGold.png'},
    rose: {src:'/__static__/devices/iPhone6PlusRose.png'}
  },
  landscape: {
    width: 736,
    height: 414,
    screenLeft: 315 / 2285,
    screenTop: 106 / 1151,
    screenWidth: 1669 / 2285,
    screenHeight: 940 / 1151,
    white: {src:'/__static__/devices/iPhone6PlusWhiteLandscape.png'},
    black: {src:'/__static__/devices/iPhone6PlusBlackLandscape.png'},
    gold: {src:'/__static__/devices/iPhone6PlusGoldLandscape.png'},
    rose: {src:'/__static__/devices/iPhone6PlusRoseLandscape.png'}
  },
}, {
  name: IPAD,
  requiresPremium: true,
  properName: 'iPad',
  filenamePrefix: 'iPad',
  type: 'tablet',
  overrideName: 'ipad2151',

  deviceSizeMultiplier: 1,
  naturalMultiplier: 1,

  portrait: {
    width: 1536,
    height: 2048,
    screenLeft: 128 / 1549,
    screenTop: 217 / 2160,
    screenWidth: 1294 / 1549,
    screenHeight: 1726 / 2160,
    white: {src:'/__static__/devices/iPadWhite.png'},
    black: {src:'/__static__/devices/iPadBlack.png'},
    gold: {src:'/__static__/devices/iPadGold.png'},
    rose: {src:'/__static__/devices/iPadWhite.png'}
  },
  landscape: {
    width: 2048,
    height: 1536,
    screenLeft: 218 / 2160,
    screenTop: 126 / 1548,
    screenWidth: 1725 / 2160,
    screenHeight: 1294 / 1548,
    white: {src:'/__static__/devices/iPadWhiteLandscape.png'},
    black: {src:'/__static__/devices/iPadBlackLandscape.png'},
    gold: {src:'/__static__/devices/iPadGoldLandscape.png'},
    rose: {src:'/__static__/devices/iPadWhiteLandscape.png'}
  },

  isTablet: true,
  isIPad: true,
}, {
  name: IPADPRO,
  requiresPremium: true,
  properName: 'iPad Pro',
  filenamePrefix: 'iPad Pro',
  type: 'tablet',
  overrideName: 'ipad2151',

  deviceSizeMultiplier: 1,
  naturalMultiplier: 1,

  isTablet: true,
  isIPad: true,

  portrait: {
    width: 2048,
    height: 2732,
    screenLeft: 134 / 2108,
    screenTop: 235 / 2924,
    screenWidth: 1840 / 2108,
    screenHeight: 2455 / 2924,
    white: {src:'/__static__/devices/iPadProWhite.png'},
    black: {src:'/__static__/devices/iPadProBlack.png'},
    gold: {src:'/__static__/devices/iPadProGold.png'},
    rose: {src:'/__static__/devices/iPadProWhite.png'}
  },
  landscape: {
    width: 2732,
    height: 2048,
    screenLeft: 235 / 2924,
    screenTop: 134 / 2108,
    screenWidth: 2455 / 2924,
    screenHeight: 1840 / 2108,
    white: {src:'/__static__/devices/iPadProWhiteLandscape.png'},
    black: {src:'/__static__/devices/iPadProBlackLandscape.png'},
    gold: {src:'/__static__/devices/iPadProGoldLandscape.png'},
    rose: {src:'/__static__/devices/iPadProWhiteLandscape.png'}
  },
}];

var ANDROID = [{
  name: NEXUS_5X,
  properName: 'Nexus 5x',
  filenamePrefix: 'Nexus 5x',
  type: 'phone',
  overrideName: 'nexus5x',
  requiresPremium: true,

  naturalMultiplier: 1,

  portrait: {
    width: 1080,
    height: 1920,
    screenLeft: 112 / 1313,
    screenTop: 291 / 2525,
    screenWidth: 1081 / 1313,
    screenHeight: 1920 / 2525,
    black: {src:'/__static__/devices/Nexus5xBlack.png'}
  },
  landscape: {
    width: 1920,
    height: 1080,
    screenLeft: 291 / 2525,
    screenTop: 112 / 1313,
    screenWidth: 1920 / 2525,
    screenHeight: 1081 / 1313,
    black: {src:'/__static__/devices/Nexus5xBlackLandscape.png'}
  }
} ,{
  name: NEXUS_6P,
  properName: 'Nexus 6P',
  filenamePrefix: 'Nexus 6P',
  type: 'phone',
  overrideName: 'nexus6p',

  naturalMultiplier: 1,

  portrait: {
    width: 1440,
    height: 2560,
    screenLeft: 118 / 1684,
    screenTop: 388 / 3272,
    screenWidth: 1440 / 1684,
    screenHeight: 2560 / 3272,
    black: {src:'/__static__/devices/Nexus6PBlack.png'}
  },
  landscape: {
    width: 2560,
    height: 1440,
    screenLeft: 388 / 3272,
    screenTop: 118 / 1684,
    screenWidth: 2560 / 3272,
    screenHeight: 1440 / 1684,
    black: {src:'/__static__/devices/Nexus6PBlackLandscape.png'}
  }
}, {
  name: NEXUS_7,
  requiresPremium: true,
  properName: 'Nexus 7',
  filenamePrefix: 'Nexus 7',
  type: 'tablet',
  overrideName: 'nexus7',

  deviceSizeMultiplier: 1,
  naturalMultiplier: 1,

  isIPad: true,
  isTablet: true,

  portrait: {
    width: 1200,
    height: 1920,
    screenLeft: 172 / 1544,
    screenTop: 354 / 2626,
    screenWidth: 1200 / 1544,
    screenHeight: 1921 / 2626,
    black: {src:'/__static__/devices/Nexus7Black.png'}
  },
  landscape: {
    width: 1920,
    height: 1200,
    screenLeft: 354 / 2626,
    screenTop: 172 / 1544,
    screenWidth: 1921 / 2626,
    screenHeight: 1200 / 1544,
    black: {src:'/__static__/devices/Nexus7BlackLandscape.png'}
  }

}, {
  name: NEXUS_9,
  requiresPremium: true,
  properName: 'Nexus 9',
  filenamePrefix: 'Nexus 9',
  type: 'tablet',
  overrideName: 'nexus9',

  deviceSizeMultiplier: 1,
  naturalMultiplier: 1,

  isIPad: true,
  isTablet: true,

  portrait: {
    width: 1536,
    height: 2048,
    screenLeft: 155 / 1847,
    screenTop: 320 / 2686,
    screenWidth: 1537 / 1847,
    screenHeight: 2048 / 2686,
    black: {src:'/__static__/devices/Nexus9Black.png'}
  },
  landscape: {
    width: 2048,
    height: 1536,
    screenLeft: 320 / 2686,
    screenTop: 155 / 1847,
    screenWidth: 2048 / 2686,
    screenHeight: 1537 / 1847,
    black: {src:'/__static__/devices/Nexus9BlackLandscape.png'}
  }
}];

var PLATFORM_LIST = ['iOS','Android'];

var PLATFORMS = {
  'iOS': {
    'defaultDevice': 'iphone6',
    'devices': IOS
  },
  'Android': {
    'defaultDevice': 'nexus5x',
    'devices': ANDROID
  }
}
iter.forEach(PLATFORM_LIST, function(platform) {
  var devices = setupPlatform(platform);
  PLATFORMS[platform]['devices'] = devices;
})


function setupPlatform(platform) {
  var devices = {
    list: [],
    byName: {},
    byType: {}
  }

  iter.forEach(PLATFORMS[platform]['devices'], function(device, i) {
    devices.list.unshift(device)

    if (!devices['byType'][device.type]) {
      devices['byType'][device.type] = [];
    }
    devices['byType'][device.type].unshift(device);

    devices['byName'][device.name] = device;

    device.deviceType = device.overrideName;
    device.deviceName = device.name;

    device.naturalWidth = device.naturalMultiplier * device.portrait.width;
    device.naturalHeight = device.naturalMultiplier * device.portrait.height;

    device.portrait.naturalWidth = device.naturalWidth;
    device.portrait.naturalHeight = device.naturalHeight;

    device.landscape.naturalWidth = device.naturalHeight;
    device.landscape.naturalHeight = device.naturalWidth;

    device.resolution = device.naturalWidth+'x'+device.naturalHeight;
  });

  return devices
}


module.exports = {
  platform_list: PLATFORM_LIST,
  platforms: PLATFORMS,

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
  NEXUS_7: NEXUS_7,
  NEXUS_7_LANDSCAPE: NEXUS_7_LANDSCAPE,
  NEXUS_9: NEXUS_9,
  NEXUS_9_LANDSCAPE: NEXUS_9_LANDSCAPE,

  screenshotCanvasWrappersInContainer: function($container, platform, orientation) {
    var $phones = $container.find('.screenshot-canvas-container');
    return iter.map($phones, function($phone) {
      var options = {
        phoneColor: $phone.getData('phone-color'),
        labelPosition: $phone.getData('layout'),
        isLandscape: (orientation == 'landscape') ? true : false
      }
      var phone = PLATFORMS[platform].devices.byName[$phone.getData('name')];
      return new ScreenshotCanvasWrapper(phone, $phone, options);
    });
  }
};