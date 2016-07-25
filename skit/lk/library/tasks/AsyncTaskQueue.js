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
var util = skit.platform.util;


var AsyncTaskQueue = function() {
  this.tasks = [];

  this.progress = 0;
  this.totalProgress = 0;

  this.concurrency = 1;
  this.numRunning = 0;

  this.progressListeners_ = [];
  this.finishListeners_ = [];
  this.taskFinishedListeners_ = [];
};


AsyncTaskQueue.prototype.setConcurrency = function(num) {
  this.concurrency = num;
};


AsyncTaskQueue.prototype.addTask = function(task, opt_progressAlreadyAdded) {
  this.tasks.push(task);
  if (!opt_progressAlreadyAdded) {
    this.totalProgress += task.totalProgress;
  }

  util.nextTick(this.maybeStart_, this);
};


AsyncTaskQueue.prototype.addExpectedProgress = function(progress) {
  this.totalProgress += progress;
};


AsyncTaskQueue.prototype.addProgressListener = function(listener, opt_context) {
  this.progressListeners_.push([listener, opt_context]);
};


AsyncTaskQueue.prototype.addFinishListener = function(listener, opt_context) {
  this.finishListeners_.push([listener, opt_context]);
};


AsyncTaskQueue.prototype.addTaskFinishedListener = function(listener, opt_context) {
  this.taskFinishedListeners_.push([listener, opt_context]);
};


AsyncTaskQueue.prototype.isFinished = function() {
  return this.numRunning == 0 && this.tasks.length == 0;
};


AsyncTaskQueue.prototype.maybeStart_ = function() {
  var self = this;

  var startNext = function() {
    if (self.numRunning >= self.concurrency) {
      return;
    }

    if (!self.tasks.length) {
      return;
    }

    var task = self.tasks[0];
    self.tasks = self.tasks.slice(1, self.tasks.length);
    self.numRunning += 1;

    var lastProgress = 0;
    var onProgress = function() {
      if (lastProgress == task.progress) {
        return;
      }

      self.progress += (task.progress - lastProgress);
      lastProgress = task.progress;

      iter.forEach(self.progressListeners_, function(listenerAndContext) {
        listenerAndContext[0].call(listenerAndContext[1], self.progress, self.totalProgress);
      }, self);
    };
    var onComplete = function() {
      self.numRunning -= 1;

      if (!task.cancelled) {
        task.finish();

        iter.forEach(self.taskFinishedListeners_, function(listenerAndContext) {
          listenerAndContext[0].call(listenerAndContext[1], task);
        }, self);
      }
      onProgress();

      if (self.isFinished()) {
        iter.forEach(self.finishListeners_, function(listenerAndContext) {
          listenerAndContext[0].call(listenerAndContext[1]);
        }, self);
      } else {
        setTimeout(startNext, 0);
      }
    };

    if (!task.cancelled) {
      task.start(onComplete, onProgress);
    } else {
      util.log('Skipped canceled task...');
      onComplete();
    }
  };

  setTimeout(startNext, 0);
};


return AsyncTaskQueue;
