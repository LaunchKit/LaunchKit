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

var env = skit.platform.env;
var iter = skit.platform.iter;
var json = skit.platform.json;
var urls = skit.platform.urls;
var util = skit.platform.util;

var AsyncTask = library.tasks.AsyncTask;


var GAEUploadTask = function(fileOrUrl) {
  AsyncTask.call(this, GAEUploadTask.TOTAL_WEIGHT);

  if (fileOrUrl + '' === fileOrUrl) {
    this.imageUrl = fileOrUrl;
    this.appEnginePath = 'image_fetch';
  } else {
    this.file = fileOrUrl;
    this.appEnginePath = 'image_upload';
  }

  this.appEngineUploadId = null;

  this.retries_ = 0;
  this.dripTimeouts_ = [];
};
util.inherits(GAEUploadTask, AsyncTask);


GAEUploadTask.getBaseGAEUrl = function(opt_path) {
  if (!GAEUploadTask._GAE_URL) {
    GAEUploadTask._GAE_URL = env.get('appEngineHost');
  }
  return GAEUploadTask._GAE_URL + (opt_path || '');
};


GAEUploadTask.TOTAL_WEIGHT = 10.0;


GAEUploadTask.prototype.start = function(onComplete, onProgress) {
  var finish = function() {
    this.progress = GAEUploadTask.TOTAL_WEIGHT;
    onProgress();
    onComplete();
  };

  if (!this.file && !this.imageUrl) {
    finish();
    return;
  }

  var xhr = new XMLHttpRequest();
  xhr.open('POST', GAEUploadTask.getBaseGAEUrl(this.appEnginePath));

  xhr.onreadystatechange = util.bind(function() {
    if (xhr.readyState != 4) {
      return;
    }

    var success = xhr.status == 200;

    if (!success && this.retries_ < 3) {
      this.retries_ += 1;

      iter.forEach(this.dripTimeouts_, function(timeout) {
        clearTimeout(timeout);
      }, this);
      this.dripTimeouts_ = [];
      this.progress = 0;

      setTimeout(util.bind(function() {
        this.start(onComplete, onProgress);
      }, this), 0);

      return;
    }

    if (success) {
      var parsed = {};
      try {
        parsed = json.parse(xhr.responseText) || {};
      } catch (e) {}

      var uploadId = parsed['uploadId'];
      this.appEngineUploadId = uploadId;
    }

    finish();
  }, this);

  var initiatedFinale_ = false;
  xhr.upload.onprogress = util.bind(function(evt) {
    if (!evt.lengthComputable) {
      return;
    }

    var floatProgress = (evt.loaded / evt.total);
    this.progress = floatProgress * (GAEUploadTask.TOTAL_WEIGHT - 3);

    // After the file itself is uploaded, it takes awhile to process.
    // So, fake additional progress by continuing the progress bar.
    if (floatProgress == 1.0 && !initiatedFinale_) {
      initiatedFinale_ = true;
      var incrementOnce = function() {
        if (this.progress < GAEUploadTask.TOTAL_WEIGHT) {
          this.progress += 1;
          onProgress();
        }
      };
      this.dripTimeouts_.push(setTimeout(incrementOnce, 500));
      this.dripTimeouts_.push(setTimeout(incrementOnce, 1000));
      this.dripTimeouts_.push(setTimeout(incrementOnce, 1500));
    }

    onProgress();
  }, this);

  var formData = new FormData();
  if (this.file) {
    formData.append('upload', this.file);
  } else {
    formData.append('fullsize_url', this.imageUrl);
  }
  xhr.send(formData);
};


return GAEUploadTask;