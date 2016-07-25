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
var layout = skit.browser.layout;
var iter = skit.platform.iter;
var util = skit.platform.util;

var useragent = library.misc.useragent;


var FilesChooser = function($container) {
  this.selectedFiles_ = [];
  this.onFileChosenListeners_ = [];
  this.onErrorListeners_ = [];

  this.supported = FilesChooser.supported();
  if (!this.supported) {
    return;
  }

  this.$dropContainer = $container.get('.drop-target-container');
  if (this.$dropContainer) {
    this.setupDragDrop_();
  }

  // Setup file picker floating input.
  this.$pickerContainer = $container.get('.file-picker-container');
  if (this.$pickerContainer) {
    this.setupFilePicker_();
  }
};


FilesChooser.supported = function() {
  var support = {
    filereader: typeof FileReader != 'undefined',
    formdata: !!window.FormData,
    dnd: 'draggable' in document.createElement('span'),
    progress: 'upload' in (window.XMLHttpRequest ? new XMLHttpRequest : {})
  };

  return support.dnd && support.formdata && support.progress && support.filereader;
};


FilesChooser.Error = {
  TOO_BIG: 'TOO_BIG',
  BAD_FORMAT: 'BAD_FORMAT'
};


FilesChooser.ACCEPT_TYPES = {
  'image/png': 1,
  'image/jpeg': 1,
  'image/jpg': 1,
  'image/gif': 1
};


// 9.8MB. 10MB is the full request size limit for urlfetch.
FilesChooser.MAX_SIZE_BYTES = (1024 * 1024) * 9.8;
FilesChooser.MAX_SIZE_BYTES_BY_TYPE = {
  // Animated gifs that are bigger than ~2.5MB fail.
  'image/gif': (1024 * 1024) * 2.4
};


FilesChooser.prototype.setupDragDrop_ = function() {
  var $dropTarget = this.$dropContainer.get('.drop-target');

  events.bind($dropTarget, 'dragenter', function(e) {
    this.$dropContainer.addClass('droppable');
  }, this);
  events.bind($dropTarget, 'dragover', function(e) {
    // Prevent default here to allow dropping the file.
    e.preventDefault();
  }, this);
  events.bind($dropTarget, 'dragleave', function(e) {
    this.$dropContainer.removeClass('droppable');
  }, this);
  events.bind($dropTarget, 'drop', function(e) {
    e.preventDefault();

    this.$dropContainer.removeClass('droppable');
    this.$dropContainer.addClass('dropped');

    util.setTimeout(function() {
      this.$dropContainer.removeClass('dropped');
    }, 100, this);

    var evt = e.originalEvent;
    var files = evt.dataTransfer.files;
    iter.forEach(files, this.maybeAddFile_, this);
  }, this);
};


FilesChooser.prototype.showPicker = function() {
  var input = this.$pickerContainer.get('input[type=file]');
  input.element.click();
};


FilesChooser.prototype.setupFilePicker_ = function() {
  var fileInput = document.createElement('input');
  fileInput.type = 'file';  var $fileInput;
  if (!useragent.isMobile()) {
    fileInput.multiple = true;
  }
  fileInput.style.position = 'absolute';
  fileInput.style.opacity = '0';
  fileInput.style.top = '0';
  fileInput.style.left = '0';

  this.$pickerContainer.append(fileInput);

  events.bind(this.$pickerContainer, 'mousemove', function(evt) {
    var position = layout.position(this.$pickerContainer);
    var relativeTop = evt.pageY - position.top;
    var relativeLeft = evt.pageX - position.left;

    var width = layout.width(fileInput);
    var height = layout.height(fileInput);
    fileInput.style.left = relativeLeft - (width - 20) + 'px';
    fileInput.style.top = relativeTop - (height / 2) + 'px';
  }, this);

  events.bind(fileInput, 'change', function() {
    var files = fileInput.files;
    if (!files.length) {
      return;
    }

    iter.forEach(files, this.maybeAddFile_, this);

    fileInput.value = null;
  }, this);
};


FilesChooser.prototype.maybeAddFile_ = function(file) {
  if (file.slice || file.webkitSlice || file.mozSlice) {
    // NOTE: This has a varying API when doing start > 0: the second
    // parameter is either length or end position depending on browser.
    var blob = (file.webkitSlice || file.mozSlice || file.slice).call(file, 0, 4);

    var reader = new FileReader();
    reader.onload = util.bind(function() {
      var buffer = reader.result;
      var array = new Int32Array(buffer);
      var magicNumber = array[0];

      var type;
      // Magic numbers from:
      //   http://www.htmlgoodies.com/html5/tutorials/determine-an-images-type-using-the-javascript-filereader.html
      switch (magicNumber) {
        case 1196314761:
          type = 'image/png';
          break;
        case 944130375:
          type = 'image/gif';
          break;
        case 544099650:
          type = 'image/bmp';
          break;
        case -520103681:
        case -503326465:
          type = 'image/jpeg';
          break;
        default:
          break;
      }

      if (!type) {
        type = file.type;
      }

      this.maybeAddFileWithType_(file, type);
    }, this);
    reader.readAsArrayBuffer(blob);
  } else {
    // Fall back to trusting HTML5 File API, which might provide invalid type.
    this.maybeAddFileWithType_(file, file.type);
  }
};


FilesChooser.prototype.maybeAddFileWithType_ = function(file, type) {
  if (!(type in FilesChooser.ACCEPT_TYPES)) {
    this.onError_(file, FilesChooser.Error.BAD_FORMAT);
    return;
  }

  var maxSize = FilesChooser.MAX_SIZE_BYTES_BY_TYPE[type] || FilesChooser.MAX_SIZE_BYTES;
  if (file.size > maxSize) {
    this.onError_(file, FilesChooser.Error.TOO_BIG);
    return;
  }

  this.selectedFiles_.push(file);
  this.onFileChosen_(file);
};


FilesChooser.prototype.addFileChosenListener = function(fn, opt_context) {
  this.onFileChosenListeners_.push([fn, opt_context]);
};


FilesChooser.prototype.addErrorListener = function(fn, opt_context) {
  this.onErrorListeners_.push([fn, opt_context]);
};


FilesChooser.prototype.getSelectedFiles = function() {
  return this.selectedFiles_.slice();
};


FilesChooser.prototype.onFileChosen_ = function(file) {
  iter.forEach(this.onFileChosenListeners_, function(listenerAndContext) {
    listenerAndContext[0].call(listenerAndContext[1], file);
  });
};


FilesChooser.prototype.onError_ = function(file, errorType) {
  iter.forEach(this.onErrorListeners_, function(listenerAndContext) {
    listenerAndContext[0].call(listenerAndContext[1], file, errorType);
  }, this);
};


return FilesChooser;
