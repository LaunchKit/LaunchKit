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
var net = skit.platform.net;
var util = skit.platform.util;

var LKAPIClient = library.api.LKAPIClient;
var AmbiguousProgressOverlay = library.overlays.AmbiguousProgressOverlay;
var ButtonOverlay = library.overlays.ButtonOverlay;
var FilesChooser = library.uploads.FilesChooser;
var GAEUploadTask = library.uploads.GAEUploadTask;
var devices = library.screenshots.devices;
var AsyncTaskQueue = library.tasks.AsyncTaskQueue;


var uploadImageFile = function(file, endpoint, onSuccess, context) {
  var spinner = new AmbiguousProgressOverlay();
  spinner.show();

  var showErrorMessage = function() {
    var okay = new ButtonOverlay('Whoops!', 'We ran into a problem uploading that image.');
    okay.addButton('Okay');
    okay.show();
  };

  var task = new GAEUploadTask(file);
  task.start(util.bind(function() {
    if (!task.appEngineUploadId) {
      spinner.done();
      showErrorMessage();
      return;
    }

    var dontHideSpinner = false;
    var LKAPIClientMethod = util.bind(endpoint, LKAPIClient);
    var image = LKAPIClientMethod(task.appEngineUploadId, {
      onSuccess: function(image) {
        dontHideSpinner = onSuccess.call(context, image);
      },
      onError: function() {
        showErrorMessage();
      },
      onComplete: function() {
        if (!dontHideSpinner) {
          spinner.done();
        }
      },
      context: this
    });

  }, this), util.bind(function() {}, this));
};


var uploadImageUrl = function(imageUrl, onSuccess, context) {
  var spinner = new AmbiguousProgressOverlay();
  spinner.show();

  var showTryAgain = function() {
    var okay = new ButtonOverlay('Whoops!', 'We ran into a problem uploading that image.');
    okay.addButton('Try Again', function() {
      uploadImageUrl(imageUrl);
    });
    okay.addButton('Okay');
    okay.show();
  };

  var GAEUrl = GAEUploadTask.getBaseGAEUrl() + 'image_fetch';
  net.send(GAEUrl, {
    method: 'POST',
    params: {'fullsize_url': imageUrl},
    complete: function(response) {
      if (response.status != 200) {
        showTryAgain();
        return;
      }

      var gaeId = response.body['uploadId'];
      var image = LKAPIClient.screenshotWithUploadId(gaeId, {
        onSuccess: function(image) {
          onSuccess.call(context, image);
        },
        onError: function() {
          showTryAgain();
        },
        onComplete: function() {
          spinner.done();
        },
        context: this
      });
    },
    context: this
  });
};


var uploadWebsiteImages = function(iconUrl, screenshotUrls, onFinish, context) {
  var spinner = new AmbiguousProgressOverlay('Uploading images to our server...');
  spinner.show();

  var screenshotImages = [];
  var iconImage;
  var anyErrors = false;

  var totalRemaining = screenshotUrls.length + (iconUrl ? 1 : 0);
  function maybeFinish() {
    totalRemaining--;
    if (!totalRemaining) {
      spinner.done();
      onFinish.call(context, iconImage, screenshotImages);
    }
  }

  var queue = new AsyncTaskQueue();

  iter.forEach(screenshotUrls, function(screenshotUrl, i) {
    var task = new GAEUploadTask(screenshotUrl);
    task.addFinishListener(function() {
      LKAPIClient.websiteScreenshotWithUploadId(task.appEngineUploadId, {
        onSuccess: function(image) {
          screenshotImages.push(image);
        },
        onError: function() {
          anyErrors = true;
        },
        onComplete: maybeFinish,
        context: this
      });
    }, this);
    queue.addTask(task);
  }, this);

  if (iconUrl) {
    var iconTask = new GAEUploadTask(iconUrl);
    iconTask.addFinishListener(function() {
      LKAPIClient.websiteIconWithUploadId(iconTask.appEngineUploadId, {
        onSuccess: function(image) {
          iconImage = image;
        },
        onError: function() {
          anyErrors = true;
        },
        onComplete: maybeFinish,
        context: this
      });
    }, this);
    queue.addTask(iconTask);
  }
};


function ScreenshotFileChooser($element, onChosen, onChosenContext) {
  this.filesChooser = new FilesChooser($element);
  this.filesChooser.addFileChosenListener(this.onFileChosen, this);
  this.filesChooser.addErrorListener(this.onFileError, this);

  this.onChosen = onChosen;
  this.onChosenContext = onChosenContext;
}

ScreenshotFileChooser.prototype.onFileChosen = function(file) {
  var reader = new FileReader();
  reader.onload = util.bind(function(evt) {
    var image = new Image();

    image.onerror = util.bind(function() {
      this.showFilePickerError();
    }, this);

    image.onload = util.bind(function() {
      uploadImageFile(file, LKAPIClient.screenshotWithUploadId,
          this.onChosen, this.onChosenContext);
    }, this);

    image.src = evt.target.result;
  }, this);
  reader.readAsDataURL(file);
};

ScreenshotFileChooser.prototype.onFileError = function() {
  this.showFilePickerError();
};

ScreenshotFileChooser.prototype.showFilePickerError = function() {
  var overlay = new ButtonOverlay('Screenshots Only',
      'Sorry, that aspect ratio is not supported at this time.');
  overlay.addButton('Choose Another', function() {
    this.filesChooser.showPicker();
  }, this);
  overlay.addButton('Cancel');
  overlay.show();
};



function BackgroundFileChooser($element, onChosen, onChosenContext) {
  this.filesChooser = new FilesChooser($element);
  this.filesChooser.addFileChosenListener(this.onFileChosen, this);
  this.filesChooser.addErrorListener(this.onFileError, this);

  this.onChosen = onChosen;
  this.onChosenContext = onChosenContext;
}

BackgroundFileChooser.prototype.onFileChosen = function(file) {
  var reader = new FileReader();
  reader.onload = util.bind(function(evt) {
    var image = new Image();

    image.onerror = util.bind(function() {
      this.showFilePickerError();
    }, this);

    image.onload = util.bind(function() {
      uploadImageFile(file, LKAPIClient.backgroundWithUploadId,
          this.onChosen, this.onChosenContext);
    }, this);

    image.src = evt.target.result;
  }, this);
  reader.readAsDataURL(file);
};

BackgroundFileChooser.prototype.onFileError = function() {
  this.showFilePickerError();
};

BackgroundFileChooser.prototype.showFilePickerError = function() {
  var overlay = new ButtonOverlay('Images Only',
      'Sorry, we ran into a problem reading that image.');
  overlay.addButton('Choose Another', function() {
    this.filesChooser.showPicker();
  }, this);
  overlay.addButton('Cancel');
  overlay.show();
};


function WebsiteIconFileChooser($element, onChosen, onChosenContext) {
  this.filesChooser = new FilesChooser($element);
  this.filesChooser.addFileChosenListener(this.onFileChosen, this);
  this.filesChooser.addErrorListener(this.onFileError, this);

  this.onChosen = onChosen;
  this.onChosenContext = onChosenContext;
}

WebsiteIconFileChooser.prototype.onFileChosen = function(file) {
  var reader = new FileReader();
  reader.onload = util.bind(function(evt) {
    var image = new Image();

    image.onerror = util.bind(function() {
      this.showFilePickerError();
    }, this);

    image.onload = util.bind(function() {
      uploadImageFile(file, LKAPIClient.websiteIconWithUploadId,
          this.onChosen, this.onChosenContext);
    }, this);

    image.src = evt.target.result;
  }, this);
  reader.readAsDataURL(file);
};

WebsiteIconFileChooser.prototype.onFileError = function() {
  this.showFilePickerError();
};

WebsiteIconFileChooser.prototype.showFilePickerError = function() {
  // TODO(keith) - better error message, when enforcing aspect ratio
  var overlay = new ButtonOverlay('Images Only',
      'Sorry, we ran into a problem reading that image.');
  overlay.addButton('Choose Another', function() {
    this.filesChooser.showPicker();
  }, this);
  overlay.addButton('Cancel');
  overlay.show();
};



function WebsiteLogoFileChooser($element, onChosen, onChosenContext) {
  this.filesChooser = new FilesChooser($element);
  this.filesChooser.addFileChosenListener(this.onFileChosen, this);
  this.filesChooser.addErrorListener(this.onFileError, this);

  this.onChosen = onChosen;
  this.onChosenContext = onChosenContext;
}

WebsiteLogoFileChooser.prototype.onFileChosen = function(file) {
  var reader = new FileReader();
  reader.onload = util.bind(function(evt) {
    var image = new Image();

    image.onerror = util.bind(function() {
      this.showFilePickerError();
    }, this);

    image.onload = util.bind(function() {
      uploadImageFile(file, LKAPIClient.websiteLogoWithUploadId,
          this.onChosen, this.onChosenContext);
    }, this);

    image.src = evt.target.result;
  }, this);
  reader.readAsDataURL(file);
};

WebsiteLogoFileChooser.prototype.onFileError = function() {
  this.showFilePickerError();
};

WebsiteLogoFileChooser.prototype.showFilePickerError = function() {
  // TODO(keith) - better error message, when enforcing aspect ratio
  var overlay = new ButtonOverlay('Images Only',
      'Sorry, we ran into a problem reading that image.');
  overlay.addButton('Choose Another', function() {
    this.filesChooser.showPicker();
  }, this);
  overlay.addButton('Cancel');
  overlay.show();
};


function WebsiteBackgroundFileChooser($element, onChosen, onChosenContext) {
  this.filesChooser = new FilesChooser($element);
  this.filesChooser.addFileChosenListener(this.onFileChosen, this);
  this.filesChooser.addErrorListener(this.onFileError, this);

  this.onChosen = onChosen;
  this.onChosenContext = onChosenContext;
}

WebsiteBackgroundFileChooser.prototype.onFileChosen = function(file) {
  var reader = new FileReader();
  reader.onload = util.bind(function(evt) {
    var image = new Image();

    image.onerror = util.bind(function() {
      this.showFilePickerError();
    }, this);

    image.onload = util.bind(function() {
      uploadImageFile(file, LKAPIClient.websiteBackgroundWithUploadId,
          this.onChosen, this.onChosenContext);
    }, this);

    image.src = evt.target.result;
  }, this);
  reader.readAsDataURL(file);
};

WebsiteBackgroundFileChooser.prototype.onFileError = function() {
  this.showFilePickerError();
};

WebsiteBackgroundFileChooser.prototype.showFilePickerError = function() {
  // TODO(keith) - better error message, when enforcing aspect ratio
  var overlay = new ButtonOverlay('Images Only',
      'Sorry, we ran into a problem reading that image.');
  overlay.addButton('Choose Another', function() {
    this.filesChooser.showPicker();
  }, this);
  overlay.addButton('Cancel');
  overlay.show();
};


function WebsiteScreenshotFileChooser($element, onChosen, onChosenContext) {
  this.filesChooser = new FilesChooser($element);
  this.filesChooser.addFileChosenListener(this.onFileChosen, this);
  this.filesChooser.addErrorListener(this.onFileError, this);

  this.onChosen = onChosen;
  this.onChosenContext = onChosenContext;
}

WebsiteScreenshotFileChooser.prototype.onFileChosen = function(file) {
  var reader = new FileReader();
  reader.onload = util.bind(function(evt) {
    var image = new Image();

    image.onerror = util.bind(function() {
      this.showFilePickerError();
    }, this);

    image.onload = util.bind(function() {
      uploadImageFile(file, LKAPIClient.websiteScreenshotWithUploadId,
          this.onChosen, this.onChosenContext);
    }, this);

    image.src = evt.target.result;
  }, this);
  reader.readAsDataURL(file);
};

WebsiteScreenshotFileChooser.prototype.onFileError = function() {
  this.showFilePickerError();
};

WebsiteScreenshotFileChooser.prototype.showFilePickerError = function() {
  var overlay = new ButtonOverlay('Images Only',
      'Sorry, we ran into a problem reading that image.');
  overlay.addButton('Choose Another', function() {
    this.filesChooser.showPicker();
  }, this);
  overlay.addButton('Cancel');
  overlay.show();
};


module.exports = {
  ScreenshotFileChooser: ScreenshotFileChooser,
  BackgroundFileChooser: BackgroundFileChooser,
  WebsiteIconFileChooser: WebsiteIconFileChooser,
  WebsiteLogoFileChooser: WebsiteLogoFileChooser,
  WebsiteBackgroundFileChooser: WebsiteBackgroundFileChooser,
  WebsiteScreenshotFileChooser: WebsiteScreenshotFileChooser,
  uploadImageUrl: uploadImageUrl,
  uploadWebsiteImages: uploadWebsiteImages,
  uploadImageFile: uploadImageFile
}
