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
var dom = skit.browser.dom;
var events = skit.browser.events;
var Controller = skit.platform.Controller;
var PubSub = skit.platform.PubSub;
var iter = skit.platform.iter;
var navigation = skit.platform.navigation;
var string = skit.platform.string;
var util = skit.platform.util;

var LKAPIClient = library.api.LKAPIClient;
var Dashboard = library.controllers.Dashboard;
var inlineeditable = library.misc.inlineeditable;
var AmbiguousProgressOverlay = library.overlays.AmbiguousProgressOverlay;
var ButtonOverlay = library.overlays.ButtonOverlay;
var DuplicateSetOverlay = library.screenshots.DuplicateSetOverlay;
var ScreenshotCanvasWrapper = library.screenshots.ScreenshotCanvasWrapper;
var ScreenshotFormWrapper = library.screenshots.ScreenshotFormWrapper;
var FullResolutionPreviewOverlay = library.screenshots.FullResolutionPreviewOverlay;
var devices = library.screenshots.devices;
var uploadui = library.screenshots.uploadui;
var bootstrapcolorpicker = third_party.bootstrapcolorpicker;

var html = __module__.html;
var columnHtml = __module__.column.html;
var overrideHtml = __module__.override.html;
var backgroundManagerHtml = __module__.background_manager.html;


var CANVAS_CONTAINER_SELECTOR = '.screenshot-canvas-container';
var SCREENSHOT_COLUMN_SELECTOR = '.screenshot-set-column';

var KEY_CODE_TAB = 9;
var KEY_CODE_ENTER = 13;


module.exports = Controller.create(Dashboard, {
  fullWidthContent: true,

  __preload__: function(done) {
    LKAPIClient.screenshotSetAndShots(this.params['__id__'], {
      onSuccess: function(set, shots) {
        this.set = set;
        this.shots = shots;
        this.renderTime = +(new Date());
      },
      onError: function() {
        navigation.notFound();
      },
      onComplete: done,
      context: this
    });
  },

  __load__: function() {
    this.platform = devices.platforms[this.set.platform];
    this.phone = this.platform.devices.byName[this.platform.defaultDevice];
  },

  __title__: function() {
    return 'Screenshots for ' + this.set['name'] + ' - ' + this.set['version'];
  },

  configFromShot: function(shot) {
    proPositions = [];
    iter.forEach(ScreenshotFormWrapper.POSITIONS, function(position){
      if (position.proRequired) {
        proPositions.push(position);
      }
    });

    return {
      phone: this.phone,
      positions: ScreenshotFormWrapper.POSITIONS,
      proPositions: proPositions,
      shot: shot,
      dimensions: (shot.isLandscape) ? this.phone['landscape'] : this.phone['portrait'],
      platform: this.set.platform,
      deviceOverrides: {
        phones: this.platform.devices.byType['phone'],
        tablets: this.platform.devices.byType['tablet']
      }
    };
  },

  __body__: function() {
    var configs = iter.map(this.shots, this.configFromShot, this);

    var firstShot = this.shots[0] || {};
    var fonts = ScreenshotFormWrapper.getFonts(firstShot['font']);
    var manualFontEntry = '';
    if (!iter.find(fonts, function(f) { return f.selected })) {
      manualFontEntry = firstShot['font'];
    }
    var sizes = ScreenshotFormWrapper.getFontSizes(firstShot['fontSize']);
    var weights = ScreenshotFormWrapper.getFontWeights(firstShot['fontWeight']);

    return {
      content: html({
        set: this.set,
        configs: configs,

        fonts: fonts,
        sizes: sizes,
        weights: weights,
        manualFontEntry: manualFontEntry
      })
    };
  },

  __ready__: function() {
    if (history.state && history.state.lastUpdateTime && (history.state.lastUpdateTime > this.renderTime)) {
      this.reload();
    }

    this.setupCanvases();
    this.setupAddNextShot();
    this.adjustLandscapeHeights();

    events.bind(window, 'resize', this.adjustLandscapeHeights, this)

    var $set = dom.get('#screenshot-set');
    this.delegate($set, 'textarea', 'keydown', function(evt) {
      if (evt.keyCode != 9 || (evt.metaKey || evt.ctrlKey)) {
        return;
      }

      // On tab press...
      var $col = evt.target.up(SCREENSHOT_COLUMN_SELECTOR);
      var $cols = $set.find(SCREENSHOT_COLUMN_SELECTOR);
      var index = iter.indexOf($cols, function($li) {
        return $li.element === $col.element;
      });

      var $nextCol = $cols[(index + 1) % $cols.length];
      if (evt.shiftKey) {
        var previousIndex = index == 0 ? $cols.length - 1 : index - 1;
        $nextCol = $cols[previousIndex];
      }

      if ($nextCol) {
        evt.preventDefault();

        var textarea = $nextCol.get('textarea');
        textarea = textarea.element;
        textarea.focus();
        textarea.select();
      }
    }, this);

    // Setup global font editing form.
    var $fontForm = dom.get('#screenshot-set-font-form');
    this.fontFormWrapper = new ScreenshotFormWrapper($fontForm);
    this.fontFormWrapper.addChangeListener(function() {
      var fontConfig = this.fontFormWrapper.getConfig();
      iter.forEach(this.formWrappers, function(fw) {
        for (var k in fontConfig) {
          fw.setConfig(k, fontConfig[k]);
        }
        fw.notifyChanged();
      });
    }, this);

    this.$saving = dom.get('#saving-indicator');
    this.savingCount = 0;

    inlineeditable.init();

    var pubsub = PubSub.sharedPubSub();
    pubsub.subscribe(inlineeditable.EDITABLE_SHOULD_COMMIT, this.onShouldCommitEditable, this);
    pubsub.subscribe(inlineeditable.EDITABLE_DID_COMMIT, this.onDidCommitEditable, this);
    pubsub.subscribe(inlineeditable.EDITABLE_WILL_COMMIT, this.onWillCommitEditable, this);
  },

  pageChanged: function() {
    this.adjustLandscapeHeights();
    history.replaceState({lastUpdateTime: this.renderTime+1}, '', window.location.pathname);
  },

  setupColumn: function(shot, $col) {
    var shotId = shot['id'];
    var position = shot['labelPosition'];
    var formConfig = {
      'label': shot['label'],
      'label_position': position,
      'background_color': shot['backgroundColor'],

      'font': shot['font'],
      'font_size': shot['fontSize'],
      'font_color': shot['fontColor'],
      'font_weight': shot['fontWeight'],

      'phone_color': shot['phoneColor'],
      'is_landscape': shot['isLandscape']
    };

    $col.setData('label-position', position);
    $col.addClass('position-' + position);

    var canvasWrapper = new ScreenshotCanvasWrapper(this.phone, $col.get(CANVAS_CONTAINER_SELECTOR), shot);
    var formWrapper = new ScreenshotFormWrapper($col.get('form'), formConfig);
    formWrapper.addChangeListener(function() {
      var config = formWrapper.getConfig();
      var oldPosition = $col.getData('label-position');
      var newPosition = config['label_position'];

      if (oldPosition != newPosition) {
        $col.removeClass('position-' + oldPosition);
        $col.addClass('position-' + newPosition);
        $col.setData('label-position', newPosition);
      }

      formWrapper.updateCanvasWrapper(canvasWrapper);
      this.saveShot(shotId);
    }, this);

    formWrapper.updateCanvasWrapper(canvasWrapper);

    canvasWrapper.setScreenshotImageWithUrl(shot['screenshot']['imageUrls']['full']);
    if (shot['background']) {
      canvasWrapper.setBackgroundImageWithUrl(shot['background']['imageUrls']['full']);
    }

    this.setupBackgroundFileChooser($col.get('.background-form-group'), canvasWrapper, formWrapper, shot);

    new uploadui.ScreenshotFileChooser($col.get('.change-screenshot-panel'), function(image) {
      canvasWrapper.setScreenshotImageWithUrl(image['imageUrls']['full']);
      formWrapper.setConfig('screenshot_image_id', image['id']);
      formWrapper.notifyChanged();
    }, this);

    $col.find('.screenshot-override').forEach(function(override){
      this.setupOverride(override, shot)
    }, this)

    this.setupColorPicker(formWrapper);
    this.canvasWrappers.push(canvasWrapper);
    this.formWrappers.push(formWrapper);
  },

  setupCanvases: function() {
    var columns = dom.find(SCREENSHOT_COLUMN_SELECTOR);

    this.formWrappers = [];
    this.canvasWrappers = [];
    iter.forEach(columns, function(column, i) {
      var shot = this.shots[i];
      this.setupColumn(shot, column);
    }, this);
  },

  setupAddNextShot: function() {
    this.$addNext = dom.get('#add-another-screenshot');
    new uploadui.ScreenshotFileChooser(this.$addNext, function(image) {
      this.addAnotherShotWithImage(image);
    }, this);
  },

  saveShot: function(id) {
    var propName = 'saveShotTimeout' + id;
    if (this[propName]) {
      clearTimeout(this[propName]);
    }

    this[propName] = util.setTimeout(function() {
      delete this[propName];
      this.saveShot_(id);
    }, 500, this);
  },

  saveShot_: function(id) {
    var i = iter.indexOf(this.shots, function(s) { return s['id'] == id });
    var shot = this.shots[i];
    var form = this.formWrappers[i];

    var params = form.getConfig();
    if (!this.lastSaved) {
      this.lastSaved = {};
    }

    var anyChanges = false;
    var lastSaved = this.lastSaved[id] || {};
    for (var k in params) {
      if (params[k] != lastSaved[k]) {
        anyChanges = true;
        break;
      }
    }
    for (var k in lastSaved) {
      if (params[k] != lastSaved[k]) {
        anyChanges = true;
        break;
      }
    }

    if (!anyChanges) {
      return;
    }

    this.lastSaved[id] = params;

    this.savingCount += 1;
    this.$saving.removeClass('saved');
    this.$saving.addClass('saving');

    LKAPIClient.updateShot(this.set['id'], shot['id'], params, {
      onSuccess: function(newShot) {
        var newIndex = iter.indexOf(this.shots, function(oldShot) {
          return oldShot['id'] == newShot['id'];
        });
        this.shots[newIndex] = newShot;
        this.pageChanged();
      },
      onError: function() {
        if (this.errorShown) {
          return;
        }

        this.errorShown = true;
        var error = new ButtonOverlay('Error saving edits', 'Looks like there was an error saving the changes you just made.');
        error.addButton('Try Again', function() {
          this.saveShot_(shot['id']);
        }, this);
        error.addButton('Reload Page', function() {
          navigation.navigate(navigation.relativeUrl());
        });
        error.addDissmissListener(function() {
          delete this.errorShown;
        }, this);
        error.show();
      },
      onComplete: function() {
        this.savingCount--;
        if (this.savingCount == 0) {
          this.$saving.addClass('saved');
          this.$saving.removeClass('saving');
        }
      },
      context: this
    });
  },

  addAnotherShotWithImage: function(image) {
    var lastForm = this.formWrappers[this.formWrappers.length - 1];
    var lastShot = this.shots[this.shots.length - 1];

    var params = ScreenshotFormWrapper.getDefaultConfig();
    if (lastForm) {
      params = lastForm.getConfig();
    }

    params['is_landscape'] = (image.width > image.height) ? true : false;

    params['screenshot_image_id'] = image['id'];
    params['background_image_id'] = lastShot && lastShot['background'] && lastShot['background']['id'];

    var spinner = new AmbiguousProgressOverlay();
    spinner.show();

    LKAPIClient.addShot(this.set['id'], params, {
      onSuccess: function(shot) {
        this.shots.push(shot);

        var config = this.configFromShot(shot);
        var shotHtml = columnHtml(config);

        var addNext = this.$addNext.element;
        var $col = ElementWrapper.fromHtml(shotHtml);
        addNext.parentNode.insertBefore($col.element, addNext);

        this.setupColumn(shot, $col);
        this.pageChanged();
      },
      onComplete: function() {
        spinner.done();
      },
      context: this
    });
  },

  getShotById: function(shotId) {
    var i = iter.indexOf(this.shots, function(s) { return s['id'] == shotId });
    return this.shots[i];
  },

  handleAction: function(name, $target) {
    Dashboard.prototype.handleAction.call(this, name, $target);

    switch (name) {
      case 'remove-shot':
        var id = $target.getData('id');
        this.maybeRemoveShot(id);
        break;

      case 'remove-background':
        var id = $target.getData('id');
        this.maybeRemoveShotBackground($target, id);
        break;

      case 'maybe-delete-set':
        this.maybeDeleteSet();
        break;

      case 'maybe-duplicate-set':
        this.maybeDuplicateSet();
        break;

      case 'remove-override':
        var shot = this.getShotById($target.getData('id'));
        var deviceType = $target.getData('device-type');
        this.removeOverride($target, shot, deviceType);
        break;

      case 'view-override':
        var i = iter.indexOf(this.shots, function(s) { return s['id'] == $target.getData('id') });
        var deviceType = $target.getData('device-type');
        var deviceName = $target.getData('device-name');
        this.viewOverride(i, this.shots[i], deviceType, deviceName);
        break;
    }
  },

  toggleLandscape: function($target, formwrapper, $col) {
    var checked = $target.getChecked();
    formwrapper.setConfig('is_landscape', checked);
    formwrapper.notifyChanged();
    if (checked) {
      $col.addClass('show-landscape')
    } else {
      $col.removeClass('show-landscape')
    }
  },

  maybeRemoveShot: function(shotId) {
    if (this.shots.length == 1) {
      var shot = new ButtonOverlay('Last screenshot', 'Please add another screenshot before removing the last one in the set.');
      shot.addButton('Okay');
      shot.show();
      return;
    }

    var confirm = new ButtonOverlay('Really remove this screenshot?', 'There is no undo.');
    confirm.addButton('Delete', function() {
      var i = iter.indexOf(this.shots, function(shot) {
        return shot['id'] == shotId;
      });

      this.shots.splice(i, 1);
      this.formWrappers.splice(i, 1);
      this.canvasWrappers.splice(i, 1);

      var columns = dom.find(SCREENSHOT_COLUMN_SELECTOR);
      columns[i].remove();

      // TODO(Taylor): Add it back if it fails?
      LKAPIClient.deleteShot(this.set['id'], shotId, {
        onSuccess: function(){
          this.pageChanged();
        },
        context: this
      });
    }, this);
    confirm.addButton('Cancel');
    confirm.show();
  },

  maybeRemoveShotBackground: function($el, shotId) {
    var i = iter.indexOf(this.shots, function(shot) {
      return shot['id'] == shotId;
    });

    var formWrapper = this.formWrappers[i];
    formWrapper.setConfig('background_image_id', '');
    formWrapper.notifyChanged();
    this.saveShot(shotId);

    delete this.shots[i]['background'];

    var cw = this.canvasWrappers[i];
    cw.removeBackgroundImage();

    var backgroundForm = $el.up('.background-form-group');
    backgroundForm.replaceWith(backgroundManagerHtml(this.shots[i]));

    this.setupBackgroundFileChooser(backgroundForm, cw, formWrapper, this.shots[i]);
  },

  maybeDeleteSet: function() {
    var confirm = new ButtonOverlay('Really delete this screenshot set?', 'There is no undo.');
    confirm.addButton('Delete', function() {
      LKAPIClient.deleteScreenshotSet(this.set['id'], {
        onSuccess: function() {
          navigation.navigate('/screenshots/dashboard/?deleted=1');
        },
        onError: function(response) {
          var problem = new ButtonOverlay('Whoops!', 'We ran into a problem deleting this set, please try again in a moment.');
          problem.addButton('Okay');
          problem.show();
        },
        context: this
      });
    }, this);
    confirm.addButton('Cancel');
    confirm.show();
  },

  maybeDuplicateSet: function() {
    var duplicate = new DuplicateSetOverlay(this.set);
    duplicate.show();
  },

  onShouldCommitEditable: function(editable, e, doCommit) {
    // Pretty much always save changes.
    if (!e.keyCode || e.keyCode == KEY_CODE_TAB || e.keyCode == KEY_CODE_ENTER) {
      doCommit();
    }
  },
  onWillCommitEditable: function(editable, text, cancel) {
    if (!string.trim(text)) {
      cancel();
    }
  },

  onDidCommitEditable: function(editable, text) {
    var $editable = (new ElementWrapper(editable));

    var field = 'name';
    if ($editable.hasClass('version')) {
      field = 'version'
    }

    var $warning = dom.get('#untitled-name-warning');
    if ($warning) {
      $warning.remove();
    }

    var fields = {};
    fields[field] = text;

    var original = this.set[field];
    this.set[field] = text;

    LKAPIClient.updateScreenshotSet(this.set['id'], fields, {
      onSuccess: function() {
        this.pageChanged();
      },
      onError: function() {
        this.set[field] = original;
        $editable.setText(original);
      },
      context: this
    });
  },

  setupOverride: function(override, shot) {
    new uploadui.ScreenshotFileChooser(override, function(image) {
      var deviceType = override.getData('device-type');
      var deviceName = override.getData('device-name');
      this.addOverride(override, this.set['id'], shot, image['id'], deviceType, deviceName)
    }, this);
  },

  setupBackgroundFileChooser: function($el, canvasWrapper, formWrapper, shot) {
    new uploadui.BackgroundFileChooser($el, function(image) {
      canvasWrapper.setBackgroundImageWithUrl(image['imageUrls']['full']);
      formWrapper.setConfig('background_image_id', image['id']);
      formWrapper.notifyChanged();
      shot['background'] = image;
      $el.replaceWith(backgroundManagerHtml(shot));
    }, this);
  },

  addOverride: function($el, set_id, shot, image_id, deviceType, deviceName) {
    LKAPIClient.addShotOverride(set_id, shot['id'], image_id, deviceType, {
      onSuccess: function(override) {
        shot.overrides[deviceType] = override;
        override['shot'] = shot;
        override['deviceName'] = deviceName;
        $el.get('.control').replaceChildren(overrideHtml(override));
        this.pageChanged();
      },
      onError: function(code, error) {
        this.errorShown = true;
        var error = new ButtonOverlay('Error uploading override', 'Looks like there was an error trying to add an override.');
        error.addButton('Close', function() {
        }, this);
        error.show();
      },
      context: this
    });
  },

  viewOverride: function(i, shot, deviceType, deviceName) {
    var spinner = new AmbiguousProgressOverlay();
    spinner.show();
    var cw = new ScreenshotCanvasWrapper(devices.platforms[this.set.platform].devices.byName[deviceName], null, {isLandscape: shot.overrides[deviceType]['orientation']});
    this.formWrappers[i].updateCanvasWrapper(cw);
    cw.setOrientation(shot.overrides[deviceType]['orientation'])

    if (shot['background']) {
      cw.setBackgroundImageWithUrl(shot['background']['imageUrls']['full']);
    }

    cw.setScreenshotImageWithUrl(shot.overrides[deviceType]['imageUrl'], function(){
      var overlay = new FullResolutionPreviewOverlay(cw);
      overlay.show()
      spinner.done();
    });
  },

  removeOverride: function($el, shot, deviceType) {
    LKAPIClient.deleteShotOverride(this.set['id'], shot['id'], deviceType, {
      onSuccess: function(removed) {
        delete shot.overrides[deviceType];
        var filepicker = $el.up('.screenshot-override');
        $el.parent().parent().parent().replaceChildren(overrideHtml(shot));
        this.setupOverride(filepicker, shot);
        this.pageChanged();
      },
      onError: function(code, error) {
        this.errorShown = true;
        var error = new ButtonOverlay('Error removing override', 'Looks like there was an error trying to remove an override.');
        error.addButton('Close', function() {
        }, this);
        error.show();
      },
      context: this
    });
  },

  setupColorPicker: function(formWrapper) {
    $('.color-pickme').colorpicker({
      align: 'left',
      format: 'hex'
    }).on('changeColor', function(evt){
      formWrapper.notifyChanged();
    })
  },

  adjustLandscapeHeights: function() {
    var landscapeShots = dom.find('.landscape');
    if (!landscapeShots.length) return;

    var height = dom.get('#add-another-screenshot').element.scrollHeight + 2;
    var marginTop = height / 3;
    iter.forEach(landscapeShots, function(shotContainer){
      shotContainer.element.style.minHeight = height+'px';
      shotContainer.find('.phone-container')[0].element.style.marginTop = marginTop+'px';
    })
  }

});
