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

var iter = skit.platform.iter;


var WEIGHTS_TO_LOAD = [
  100,
  300,
  400,
  600,
  700,
  800
];

var FONTS = [
  {
    name: 'Open Sans',
    google: true
  },
  {
    name: 'Raleway',
    google: true
  },
  {
    name: 'Lato',
    google: true
  },
  {
    name: 'Roboto',
    google: true
  },
  {
    name: 'Oswald',
    google: true
  },
  {
    name: 'Lora',
    google: true
  },
  {
    name: 'PT Sans',
    google: true
  },
  {
    name: 'Arial'
  },
  {
    name: 'Impact'
  },
  {
    name: 'Georgia'
  },
  {
    name: 'Palatino'
  },
  {
    name: 'Tahoma'
  },
  {
    name: 'Times'
  },
  {
    name: 'Verdana'
  }
];


/**
 * Inspired by: http://stackoverflow.com/questions/4383226/
 */
function ensureFontWeightLoaded(fontName, weight, cb, context) {
  var node = document.createElement('span');
  // Characters that vary significantly among different fonts
  node.innerHTML = 'giItT1WQy@!-/#';
  // Visible - so we can measure it - but not on the screen
  node.style.position      = 'absolute';
  node.style.left          = '-10000px';
  node.style.top           = '-10000px';
  // Large font size makes even subtle changes translate to offsetWidth changes
  node.style.fontSize      = '300px';
  // Reset any font properties
  node.style.fontFamily    = 'sans-serif';
  node.style.fontVariant   = 'normal';
  node.style.fontStyle     = 'normal';
  node.style.fontWeight    = weight;
  node.style.letterSpacing = '0';
  document.body.appendChild(node);

  // Remember width with no applied web font
  var width = node.offsetWidth;

  node.style.fontFamily = fontName + ', sans-serif';

  var i = 0;
  function maybeFinish() {
    var diff = node.offsetWidth - width;
    if (diff || i > 50) {
      node.parentNode.removeChild(node);
      node = null;
      cb.call(context);
    } else {
      i++;
      setTimeout(maybeFinish, 100);
    }
  }

  maybeFinish();
}


function loadFontByName(fontName, weight, cb, context) {
  var font = iter.find(FONTS, function(font) {
    return font.name == fontName;
  });

  if (!font || !font.google) {
    cb.call(context);
    return;
  }

  var id = 'font-style-' + font.name.toLowerCase().replace(/\W+/, '-');
  if (!document.getElementById(id)) {
    var link = document.createElement('link');
    link.id = id;
    link.rel = 'stylesheet';
    link.type = 'text/css';
    link.href = '//fonts.googleapis.com/css?family=' + encodeURIComponent(font.name) + ':' + WEIGHTS_TO_LOAD.join(',');
    document.getElementsByTagName('head')[0].appendChild(link);
  }
  ensureFontWeightLoaded(font.name, weight, cb, context);
}


module.exports = {
  FONTS: FONTS,
  loadFontByName: loadFontByName,
  ensureFontWeightLoaded: ensureFontWeightLoaded
};