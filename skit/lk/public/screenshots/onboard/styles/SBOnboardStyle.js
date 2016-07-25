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
var Controller = skit.platform.Controller;
var iter = skit.platform.iter;
var json = skit.platform.json;
var object = skit.platform.object;
var navigation = skit.platform.navigation;
var string = skit.platform.string;
var urls = skit.platform.urls;
var util = skit.platform.util;

var App = library.controllers.App;
var Dashboard = library.controllers.Dashboard;
var ButtonOverlay = library.overlays.ButtonOverlay;
var FullResolutionPreviewOverlay = library.screenshots.FullResolutionPreviewOverlay;
var ScreenshotFormWrapper = library.screenshots.ScreenshotFormWrapper;
var fonts = library.screenshots.fonts;
var devices = library.screenshots.devices;
var uploadui = library.screenshots.uploadui;
var bootstrapcolorpicker = third_party.bootstrapcolorpicker;

var html = __module__.html;


module.exports = Controller.create(Dashboard, {
  enableLoggedOut: true,

  __load__: function() {
    var query = navigation.query();
    this.platform = query['platform'] || 'iOS';
    this.orientation = query['orientation'] || 'portrait';
  },

  __title__: function() {
    return 'Set screenshot styles';
  },

  __body__: function() {
    var platform = devices.platforms[this.platform];
    var topPhone = platform.devices.byName[platform.defaultDevice];
    var bottomPhones = [];
    iter.forEach(platform.devices.list, function(phone){
      bottomPhones.push({
        phone:phone,
        dimensions:phone[this.orientation]
      });
    }, this)

    var config = ScreenshotFormWrapper.getDefaultConfig();

    var layout = navigation.query()['layout'];
    var positions = ScreenshotFormWrapper.getLabelPositions(layout);
    var color = navigation.query()['color'];
    var selectedPosition = iter.find(positions, function(p) { return p.selected }).value;

    var proPositions = [];
    iter.forEach(ScreenshotFormWrapper.POSITIONS, function(position){
      if (position.proRequired) {
        proPositions.push(position);
      }
    })

    if (this.platform == 'Android') {
      config['font'] = 'Roboto';
    }

    if (this.orientation == 'landscape') {
      config['is_landscape'] = 'true';
    }

    config['phone_color'] = navigation.query()['phoneColor'];

    var fonts = ScreenshotFormWrapper.getFonts(config['font']);
    if (!iter.find(fonts, function(f) { return f.selected })) {
      config['font_manual_entry'] = config['font'];
    }

    var sizes = ScreenshotFormWrapper.getFontSizes(config['font_size']);
    var weights = ScreenshotFormWrapper.getFontWeights(config['font_weight']);

    return {
      content: html({
        'platform': this.platform,
        'topPhone': topPhone,
        'phones': bottomPhones,

        'positions': positions,
        'selectedPosition': selectedPosition,
        'proPositions': proPositions,
        'fonts': fonts,
        'sizes': sizes,
        'weights': weights,
        'phone_color': this.phoneColor,

        'dimensions': topPhone[this.orientation],

        'is_landscape': (this.orientation == 'landscape') ? true : '',

        'config': config
      })
    };
  },

  __ready__: function() {
    var screenshotId = window.sessionStorage['screenshot-id'];
    var imageUrl = window.sessionStorage['screenshot-url'];
    if (!imageUrl) {
      navigation.navigate('/screenshots/onboard/?no-saved-image=1');
      return;
    }

    $('.color-pickme').colorpicker({
      align: 'left',
      format: 'hex'
    }).on('changeColor', function(evt){
      this.onChangeFormWrapper();
    }.bind(this))

    this.$editor = dom.get('#screenshot-editor');

    this.screenshotImage = {
      id: screenshotId,
      url: imageUrl
    };

    //
    // INITIALIZE FORM
    //

    var $form = dom.get('#screenshot-form');
    this.form = new ScreenshotFormWrapper($form, $form.serializeForm());
    this.form.addChangeListener(this.onChangeFormWrapper, this);
    this.form.addSaveListener(this.onSaveFormWrapper, this);

    new uploadui.BackgroundFileChooser($form, function(image) {
      var backgroundImageUrl = image['imageUrls']['full'];

      this.backgroundImage = {
        id: image['id'],
        url: backgroundImageUrl
      };

      this.setBackgroundImageWithUrl(backgroundImageUrl);
    }, this);


    //
    // INITIALIZE PHONES
    //
    this.canvasWrappers = devices.screenshotCanvasWrappersInContainer(dom.get('body'), this.platform, this.orientation);
    iter.forEach(this.canvasWrappers, function(canvasWrapper) {
      canvasWrapper.setScreenshotImageWithUrl(imageUrl);
    }, this);

    iter.forEach(this.canvasWrappers, function(canvasWrapper) {
      this.form.updateCanvasWrapper(canvasWrapper);
    }, this);

    this.onChangeFormWrapper();
  },

  setBackgroundImageWithUrl: function(imageUrl) {
    iter.forEach(this.canvasWrappers, function(canvasWrapper) {
      canvasWrapper.setBackgroundImageWithUrl(imageUrl);
    }, this);
  },

  handleAction: function(name, $target) {
    Dashboard.prototype.handleAction.apply(this, arguments);

    switch (name) {
      case 'full-resolution-preview':
        var overlay = new FullResolutionPreviewOverlay(this.canvasWrappers[0]);
        overlay.show();
        break;
    }
  },


  // EVENT HANDLERS

  onChangeFormWrapper: function() {
    var config = this.form.getConfig();
    var position = config['label_position'];
    iter.forEach(ScreenshotFormWrapper.POSITIONS, function(p) {
      this.$editor.removeClass('position-' + p.value);
    }, this);
    this.$editor.addClass('position-' + position);

    iter.forEach(this.canvasWrappers, function(canvasWrapper) {
      this.form.updateCanvasWrapper(canvasWrapper);
    }, this);
  },

  onSaveFormWrapper: function() {
    var config = this.form.getConfig();
    window.sessionStorage['platform'] = this.platform;
    window.sessionStorage['screenshot-config'] = JSON.stringify(config);
    window.sessionStorage['screenshot-id'] = this.screenshotImage.id;
    window.sessionStorage['screenshot-url'] = this.screenshotImage.url;
    if (this.backgroundImage) {
      window.sessionStorage['background-image-id'] = this.backgroundImage.id;
      window.sessionStorage['background-image-url'] = this.backgroundImage.url;
    }

    var nextUrl = '/screenshots/onboard/name-app/';
    nextUrl = urls.appendParams('/signup/', {'redirect': nextUrl});
    navigation.navigate(nextUrl);
  }
});
