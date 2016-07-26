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
var navigation = skit.platform.navigation;
var iter = skit.platform.iter;
var urls = skit.platform.urls;
var util = skit.platform.util;
var object = skit.platform.object;

var LKAPIClient = library.api.LKAPIClient;
var Dashboard = library.controllers.Dashboard;
var AmbiguousProgressOverlay = library.overlays.AmbiguousProgressOverlay;
var ButtonOverlay = library.overlays.ButtonOverlay;
var ScreenshotCanvasWrapper = library.screenshots.ScreenshotCanvasWrapper;
var devices = library.screenshots.devices;
var AsyncTask = library.tasks.AsyncTask;
var AsyncTaskQueue = library.tasks.AsyncTaskQueue;
var GAEUploadTask = library.uploads.GAEUploadTask;
var FullResolutionPreviewOverlay = library.screenshots.FullResolutionPreviewOverlay;

var html = __module__.html;


function RenderAndConvertCanvasTask(wrapper, opt_hq) {
  AsyncTask.call(this);

  this.wrapper = wrapper;
  this.hq = !!opt_hq;
}
util.inherits(RenderAndConvertCanvasTask, AsyncTask);

RenderAndConvertCanvasTask.prototype.start = function(onComplete, onProgress) {
  var quality = 0.8;
  if (this.hq) {
    quality = 1;
  }

  var dataUrl = this.wrapper.renderToDataURL(quality);
  var blobBin = atob(dataUrl.split(',')[1]);
  delete dataUrl;

  var array = [];
  for (var i = 0; i < blobBin.length; i++) {
    array.push(blobBin.charCodeAt(i));
  }
  delete blobBin;

  if (!array.length) {
    this.file = null;
  } else {
    this.file = new Blob([new Uint8Array(array)], {type: 'image/png'});
    delete array;
  }

  // Give the browser some time to breathe in between renders,
  // because the canvas API is synchronous.
  setTimeout(onComplete, 100);
};

RenderAndConvertCanvasTask.prototype.cleanup = function() {
  delete this.file;
};


module.exports = Controller.create(Dashboard, {
  __preload__: function(done) {
    LKAPIClient.screenshotSetAndShots(this.params['__id__'], {
      onSuccess: function(set, shots) {
        this.set = set;
        this.shots = shots;
      },
      onError: function() {
        navigation.notFound();
      },
      onComplete: done,
      context: this
    });
  },

  __load__: function() {
    var configs = [];
    var allPhones = [];
    var allTablets = [];

    iter.forEach(devices.platforms[this.set.platform].devices.byType['phone'], function(phone) {
      allPhones.push(object.copy(phone));
    });

    iter.forEach(devices.platforms[this.set.platform].devices.byType['tablet'], function(tablet) {
      allTablets.push(object.copy(tablet));
    });

    var configsByPhone = [];
    iter.forEach(allPhones, function(phone) {
      var group = [];
      var groupConfig = {phone: phone, configs: group};

      iter.forEach(this.shots, function(shot, i) {
        var filename = phone.filenamePrefix + ' - Screenshot ' + (i + 1);
        var config = {
          phone: phone,
          shot: shot,
          filename: filename,
          dimensions: (shot.isLandscape) ? phone['landscape'] : phone['portrait']
        };

        group.push(config);
        configs.push(config);
      }, this);

      // only show devices that have shots
      if (group.length) {
        configsByPhone.push(groupConfig);
      }
    }, this);

    var configsByTablet = [];
    iter.forEach(allTablets, function(phone){
      var group = [];
      var groupConfig = {phone: phone, configs: group};

      iter.forEach(this.shots, function(shot, i) {

        var orientation = 'portrait';
        if (shot.overrides[phone.overrideName] && shot.overrides[phone.overrideName]['orientation']) {
          orientation = 'landscape';
        }

        var filename = phone.filenamePrefix + ' - Screenshot ' + (i + 1);
        var config = {
          phone: phone,
          shot: shot,
          filename: filename,
          dimensions: phone[orientation]
        };

        if (shot.overrides[phone.overrideName]) {
          group.push(config);
          configs.push(config);
        }

      }, this);

      if (group.length) {
        configsByTablet.push(groupConfig);
      }
    }, this)

    this.configsByPhone = configsByPhone;
    this.configsByTablet = configsByTablet;
    this.configs = configs;
    this.numImagesLoaded = 0;
    this.numImages = configs.length;
  },

  __title__: function() {
    return 'Preview ' + this.set['name'] + ' - ' + this.set['version'] + ' screenshots';
  },

  __body__: function() {
    return {
      content: html({
        set: this.set,
        configsByPhone: this.configsByPhone,
        configsByTablet: this.configsByTablet
      })
    };
  },

  __ready__: function() {
    var containers = dom.find('.screenshot-set > ul > li');
    var wrappers = [];
    iter.forEach(containers, function(container, i) {
      container.setData('canvas-id', i)
      var config = this.configs[i];
      var shot = config.shot;
      var phone = config.phone;
      var canvasWrapper = new ScreenshotCanvasWrapper(phone, container.get('.screenshot-canvas-container'), {
        isLandscape: (shot.overrides[phone.overrideName]) ? shot.overrides[phone.overrideName]['orientation'] : shot['isLandscape'],
        phoneColor: shot['phoneColor']
      });

      if (shot['background']) {
        this.numImages += 1;
        canvasWrapper.setBackgroundImageWithUrl(shot['background']['imageUrls']['full'], this.imageLoaded, this);
      }

      if (shot.overrides[phone.overrideName]) {
        var overrideImage = shot.overrides[phone.overrideName];
        canvasWrapper.setScreenshotImageWithUrl(overrideImage['imageUrl'], this.imageLoaded, this);
      } else {
        canvasWrapper.setScreenshotImageWithUrl(shot['screenshot']['imageUrls']['full'], this.imageLoaded, this);
      }

      canvasWrapper.setLabel(shot['label']);
      canvasWrapper.setLabelPosition(shot['labelPosition']);
      canvasWrapper.setPhoneColor(shot['phoneColor']);

      canvasWrapper.setFontWeight(shot['font'], shot['fontWeight']);
      canvasWrapper.setFontSize(shot['fontSize']);
      canvasWrapper.setFontColor(shot['fontColor']);

      canvasWrapper.setBackgroundColor(shot['backgroundColor']);

      wrappers.push(canvasWrapper);
    }, this);

    // NOTE: It is important that this array and the configs array
    // are in the same order.
    this.canvasWrappers = wrappers;
  },

  handleAction: function(name, $target) {
    Dashboard.prototype.handleAction.apply(this, arguments);

    switch (name) {
      case 'export-screenshots':
        var hq = !!navigation.query()['secret-hq'] || $target.getData('png') == '1';
        this.startExport(hq);
        break;

      case 'fullscreen-preview':
        this.fullscreenPreview($target.getData('canvas-id'));
        break;
    }
  },

  startExport: function(hq) {
    this.onceImagesLoad(function(){
      this.renderExportImages(hq);
    })
  },

  onceImagesLoad: function(callback) {
    var context = this;

    var isLoaded = util.bind(function(){
      return this.numImagesLoaded == this.numImages;
    }, this)

    if (isLoaded()) {
      callback.call(context);
      return
    }

    var spinner = new AmbiguousProgressOverlay('Waiting for images to load...');
    spinner.show();

    var finish = function() {
      clearInterval(interval);
      spinner.done();
      callback.call(context);
    }

    var waitLoops = 0;
    var interval = setInterval(function() {
      waitLoops += 1;

      if (isLoaded()) {
        finish();
        return;
      }

      if (waitLoops == 15) {
        spinner.setSubtext('Taking longer than expected...');
      }

      if (waitLoops >= 30) {
        clearInterval(interval);
        spinner.done();
        var overlay = new ButtonOverlay('Uhoh',
          ['Looks like some of the screenshot images are not loading. You can try reloading the page, or render anyway.']);
        overlay.addButton('Okay', function() {
          var url = urls.appendParams(navigation.relativeUrl(), {'failed_export': '1'});
          navigation.navigate(url);
        }, this);
        overlay.addButton('Render anyway', function() {
          callback.call(context)
        }, this);
        overlay.show();
      }

    }, 2000)
  },

  renderExportImages: function(hq) {
    var spinner = new AmbiguousProgressOverlay('Rendering images...');
    spinner.show();

    var renderQueue = new AsyncTaskQueue();
    var uploadQueue = new AsyncTaskQueue();
    // A lot of the upload time is spent waiting on App Engine to finish,
    // so we can probably afford to do multiple uploads at once.
    uploadQueue.setConcurrency(1);

    iter.forEach(this.canvasWrappers, function(wrapper, i) {
      var t = new RenderAndConvertCanvasTask(wrapper, hq);
      t.index = i;
      renderQueue.addTask(t);
      uploadQueue.addExpectedProgress(GAEUploadTask.TOTAL_WEIGHT);
    }, this);

    renderQueue.addTaskFinishedListener(function(t) {
      var u = new GAEUploadTask(t.file);
      u.renderTask = t;
      u.index = t.index;
      uploadQueue.addTask(u, true);
    }, this);

    var uploadNames = [];
    var uploadIds = [];
    uploadQueue.addTaskFinishedListener(function(u) {
      u.renderTask.cleanup();
      delete u.renderTask;

      var config = this.configs[u.index];
      if (u.appEngineUploadId) {
        uploadIds.push(u.appEngineUploadId);
        uploadNames.push(config.filename);
      }
    }, this);

    var hasSet = false;
    uploadQueue.addProgressListener(function(progress, total) {
      var pct = 100.0 * (progress / total);
      spinner.setProgressPercent(pct);

      if (!hasSet && renderQueue.isFinished()) {
        hasSet = true;
        spinner.setSubtext('Uploading...');
      }
    }, this);

    uploadQueue.addFinishListener(function() {
      if (!renderQueue.isFinished()) {
        return;
      }

      this.finishExport(hq, uploadIds, uploadNames, function() {
        spinner.done();
      });
    }, this);
  },

  finishExport: function(hq, uploadIds, uploadNames, onComplete) {
    var spinner = new AmbiguousProgressOverlay('Creating a zip file...',
        'Hang tight, this could take a minute or two.');
    spinner.show();

    function showError(code) {
      spinner.done();

      var overlay = new ButtonOverlay('Something went wrong',
          ['Looks like something went wrong building your bundle. (Code: ' + code + ').',
           'Please try again. If this continues to happen, please contact us and we can look into it.']);
      overlay.addButton('Okay', function() {
        var url = urls.appendParams(navigation.relativeUrl(), {'failed_export': '1'});
        navigation.navigate(url);
      }, this);
      overlay.show();
    }

    var wait = 2000;

    var checkStatus = util.bind(function(bundleId) {
      LKAPIClient.screenshotSetBundleStatus(bundleId, {
        onSuccess: function(status) {
          if (status == 'ready') {
            spinner.done();
            this.showDownloadOverlay(bundleId);
            return;
          }
          if (status == 'error') {
            showError('error-status');
            return;
          }

          setTimeout(function() {
            checkStatus(bundleId);
          }, wait);

          // slightly increase wait time with each check.
          wait *= 1.1;
        },
        onError: function(code) {
          showError(code + '-status');
        },
        context: this
      });
    }, this);

    LKAPIClient.addScreenshotSetBundle(this.set['id'], hq, uploadIds, uploadNames, {
      onSuccess: function(bundleId) {
        setTimeout(function() {
          checkStatus(bundleId);
        }, wait);
      },
      onError: function(code) {
        spinner.done();

        showError(code + '-create');
      },
      onComplete: onComplete,
      context: this
    });
  },

  showDownloadOverlay: function(bundleId) {
      var downloadUrl = urls.parse(navigation.url()).path.replace('/preview', '/download');
      downloadUrl = urls.appendParams(downloadUrl, {'bundle': bundleId});

      var wasntThatEasyUrl = '/screenshots/dashboard/?exported=1';

      var overlay = new ButtonOverlay('Screenshots are ready!');
      overlay.addLinkButton('Download', downloadUrl, {'download': ''}, function() {
        // If the download worked, this page will still be active later.
        setTimeout(function() {
          navigation.navigate(wasntThatEasyUrl);
        }, 2500);
      }, this);
      overlay.addLinkButton('Done', wasntThatEasyUrl);
      overlay.show();
  },

  fullscreenPreview: function(i) {
    var cw = this.canvasWrappers[i];

    var overlay = new FullResolutionPreviewOverlay(cw);
    overlay.show();
  },

  imageLoaded: function() {
    this.numImagesLoaded += 1;
  }

});
