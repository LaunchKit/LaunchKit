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


var AsyncTask = function(opt_totalProgress) {
  this.completed = false;
  this.cancelled = false;

  this.progress = 0;
  this.totalProgress = opt_totalProgress || 1;

  this.onFinishListeners_ = [];
};


AsyncTask.prototype.start = function(onComplete, onProgress) {};


AsyncTask.prototype.finish = function() {
  this.completed = true;
  this.progress = this.totalProgress;

  for (var i = 0; i < this.onFinishListeners_.length; i++) {
    var fnContext = this.onFinishListeners_[i];
    fnContext[0].call(fnContext[1]);
  }
};


AsyncTask.prototype.cancel = function() {
  this.cancelled = true;
};


AsyncTask.prototype.addFinishListener = function(fn, opt_context) {
  this.onFinishListeners_.push([fn, opt_context]);
};


return AsyncTask;