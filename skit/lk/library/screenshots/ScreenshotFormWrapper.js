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

var dom = skit.browser.dom;
var events = skit.browser.events;
var iter = skit.platform.iter;
var object = skit.platform.object;
var string = skit.platform.string;

var ScreenshotCanvasWrapper = library.screenshots.ScreenshotCanvasWrapper;
var fonts = library.screenshots.fonts;
var colors = library.misc.colors;


function ScreenshotFormWrapper($form, opt_config) {
  this.$form = $form;
  this.config = opt_config || $form.serializeForm();

  for (var k in this.config) {
    this.$form.setFormValue(k, this.config[k]);
  }

  // Cancel submissions on this form.
  events.bind(this.$form, 'submit', function(evt) { evt.preventDefault(); });

  var save = this.$form.get('button[type=submit]');
  if (save) {
    events.bind(save, 'click', this.onClickSave, this);
  }

  var font = this.$form.get('select[name=font]');
  if (font) {
    events.bind(font, 'change', this.resetCustomFont, this);
  }

  var fontColor = this.$form.get('input[name=font_color]');
  if (fontColor) {
    events.bind(fontColor, 'keyup', this.updateColor, this);
  }

  var backgroundColor = this.$form.get('input[name=background_color]');
  if (backgroundColor) {
    events.bind(backgroundColor, 'keyup', this.updateColor, this);
  }

  iter.forEach(this.$form.find('input, select, textarea'), function($el) {
    events.bind($el, 'change', this.onChangeForm, this);
    events.bind($el, 'keyup', this.onChangeForm, this);
  }, this);

  this.changeListeners_ = [];
  this.saveListeners_ = [];
}


ScreenshotFormWrapper.getDefaultConfig = function() {
  var bgColorOptions = [
    '#A5D9FF',
    '#DDE8ED',
    '#A1B1BA',
    '#F5F7F8',
    '#A7DBD8'
  ];
  var bgColor = bgColorOptions[Math.floor(Math.random()*bgColorOptions.length)];

  var fontOptions = [
    'Lato',
    'Open Sans',
    'Raleway',
    'PT Sans',
    'Lora'
  ];
  var font = fontOptions[Math.floor(Math.random()*fontOptions.length)];

  return {
    'label_position': ScreenshotCanvasWrapper.LABEL_POSITION_ABOVE,
    'label': 'Replace this text with your own and watch magic happen.',

    'font': font,
    'font_size': '5',
    'font_color': '#333333',
    'font_weight': '400',

    'phone_color': 'black',

    'background_color': bgColor,
    'is_landscape': false
  };
};

ScreenshotFormWrapper.POSITIONS = [
  {name: 'Cropped Device with Text Above', value: ScreenshotCanvasWrapper.LABEL_POSITION_ABOVE},
  {name: 'Cropped Device with Text Below', value: ScreenshotCanvasWrapper.LABEL_POSITION_BELOW},
  {name: 'Full Device with Text Above', value: ScreenshotCanvasWrapper.LABEL_POSITION_ABOVE_FULL_DEVICE, proRequired: true},
  {name: 'Full Device with Text Below', value: ScreenshotCanvasWrapper.LABEL_POSITION_BELOW_FULL_DEVICE, proRequired: true},
  {name: 'Full Device Only', value: ScreenshotCanvasWrapper.LABEL_POSITION_DEVICE, proRequired: true},
  {name: 'Screenshot with Text Above', value: ScreenshotCanvasWrapper.LABEL_POSITION_ABOVE_SCREENSHOT, proRequired: true},
  {name: 'Screenshot with Text Below', value: ScreenshotCanvasWrapper.LABEL_POSITION_BELOW_SCREENSHOT, proRequired: true},
  {name: 'Screenshot Only', value: ScreenshotCanvasWrapper.LABEL_POSITION_NONE, proRequired: true}
];

ScreenshotFormWrapper.getLabelPositions = function(currentValue) {
  var anySelected = false;
  var items = iter.map(ScreenshotFormWrapper.POSITIONS, function(position) {
    var opt = {name: position.name, value: position.value, proRequired: (position.proRequired) ? true : false};
    if (position.value == currentValue) {
      opt.selected = 'selected';
      anySelected = true;
    }
    return opt;
  });

  if (!anySelected) {
    items[0].selected = true;
  }
  return items;
};
ScreenshotFormWrapper.getFonts = function(currentValue) {
  return iter.map(fonts.FONTS, function(font) {
    var opt = {name: font.name, value: font.name};
    if (font.name == currentValue) {
      opt.selected = 'selected';
    }
    return opt;
  });
};
ScreenshotFormWrapper.getFontWeights = function(currentValue) {
  var options = [
    {name: 'Extra Light', value: '100'},
    {name: 'Light', value: '300'},
    {name: 'Normal', value: '400'},
    {name: 'Bold', value: '700'},
    {name: 'Extra Bold', value: '800'}
  ];
  iter.forEach(options, function(option) {
    if (option.value == currentValue) {
      option.selected = 'selected';
    }
  });
  return options;
};
ScreenshotFormWrapper.getFontSizes = function(currentValue) {
  var options = [
    {name: 'Extra Small', value: '3'},
    {name: 'Small', value: '4'},
    {name: 'Medium', value: '5'},
    {name: 'Large', value: '6'},
    {name: 'Extra Large', value: '7'}
  ];
  iter.forEach(options, function(option) {
    if (option.value == currentValue) {
      option.selected = 'selected';
    }
  });
  return options;
};
ScreenshotFormWrapper.prototype.resetCustomFont = function() {
  var customFont = this.$form.get('input[name=font_manual_entry]');
  if (customFont) {
    customFont.setValue('');
  }
};
ScreenshotFormWrapper.prototype.updateColor = function(event) {
  var color = event.target.getValue();
  if (color) {
    event.target.element.previousElementSibling.setAttribute("style", 'background-color:'+color);
  }
};
ScreenshotFormWrapper.prototype.notifyChanged = function() {
  iter.forEach(this.changeListeners_, function(fnContext) {
    fnContext[0].call(fnContext[1], this);
  }, this);
};
ScreenshotFormWrapper.prototype.notifySaved = function() {
  iter.forEach(this.saveListeners_, function(fnContext) {
    fnContext[0].call(fnContext[1], this);
  }, this);
};


ScreenshotFormWrapper.prototype.addChangeListener = function(fn, context) {
  this.changeListeners_.push([fn, context]);
};


ScreenshotFormWrapper.prototype.addSaveListener = function(fn, context) {
  this.saveListeners_.push([fn, context]);
};


ScreenshotFormWrapper.prototype.onClickSave = function(evt) {
  evt.preventDefault();
  this.notifySaved();
};


ScreenshotFormWrapper.prototype.onChangeForm = function(evt) {
  this.notifyChanged();
};


ScreenshotFormWrapper.prototype.getConfig = function() {
  var config = this.$form.serializeForm();
  for (var k in config) {
    var value = config[k];
    switch (k) {
      case 'font_color':
      case 'background_color':
        config[k] = colors.humanInputToHex(value);
        break;

      case 'font_manual_entry':
        if (string.trim(config[k])) {
          config['font'] = config[k];
        }
        config[k] = null;
        break;
    }
  }

  for (var k in config) {
    if (config[k]) {
      this.config[k] = config[k];
    } else {
      delete this.config[k];
    }
  }

  return object.copy(this.config);
};


ScreenshotFormWrapper.prototype.setConfig = function(k, v) {
  this.config[k] = v;
  this.$form.setFormValue(k, v);
};


ScreenshotFormWrapper.prototype.updateCanvasWrapper = function(canvasWrapper) {
  var config = this.getConfig();

  canvasWrapper.setLabelPosition(config['label_position']);
  canvasWrapper.setPhoneColor(config['phone_color']);
  canvasWrapper.setLabel(config['label']);

  canvasWrapper.setFontWeight(config['font'], config['font_weight']);
  canvasWrapper.setFontSize(config['font_size']);
  canvasWrapper.setFontColor(config['font_color']);

  canvasWrapper.setBackgroundColor(config['background_color']);
  canvasWrapper.setOrientation(config['is_landscape']);
};


module.exports = ScreenshotFormWrapper;