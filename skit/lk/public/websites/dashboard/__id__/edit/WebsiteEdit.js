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
var navigation = skit.platform.navigation;

var LKAPIClient = library.api.LKAPIClient;
var Dashboard = library.controllers.Dashboard;
var ButtonOverlay = library.overlays.ButtonOverlay;
var TitledOverlay = library.overlays.TitledOverlay;
var colors = library.misc.colors;
var fonts = library.screenshots.fonts;
var uploadui = library.screenshots.uploadui;
var templates = library.websites.templates;
var markdown = third_party.marked;

var html = __module__.html;
var screenshotHtml = __module__.screenshot.html;

var showErrorMessage = function() {
  var okay = new ButtonOverlay('Whoops!', 'There are some errors with the input, please correct the red fields.');
  okay.addButton('Okay');
  okay.show();
};

var showDeleteMessage = function() {
  var confirm = new ButtonOverlay('Really delete this website?', 'There is no undo.');
  confirm.addButton('Delete', function() {

    var deleteSite = function() {
      LKAPIClient.deleteWebsite(this.website['id'], {
        onSuccess: function() {
          delete this.initialForm;
          navigation.navigate('/websites/dashboard/?deleted=1');
        },
        onError: function(response) {
          var problem = new ButtonOverlay('Whoops!', 'We ran into a problem deleting this website, please try again in a moment.');
          problem.addButton('Okay');
          problem.show();
        },
        context: this
      });
    }.bind(this);

    deleteSite();
  }, this);

  confirm.addButton('Cancel');
  confirm.show();
};


module.exports = Controller.create(Dashboard, {
  __preload__: function(done) {
    var id = this.params['__id__'];
    LKAPIClient.getFullWebsite(id, {
      onSuccess: function(website) {
        this.website = website;
      },
      onError: function() {
        navigation.notFound();
      },
      onComplete: done,
      context: this
    });
  },

  __title__: function() {
    return 'Edit ' + this.website['appName'] + ' Website';
  },

  __body__: function() {
    var websiteTemplate = this.website['template']
    var template = iter.find(templates.TEMPLATES, function(s){return s.id == websiteTemplate});

    return {
      content: html({
        'fonts': fonts.FONTS,
        'template': template,
        'website': this.website
      })
    };
  },

  __ready__: function() {
    this.$form = dom.get('#app-website-edit-form');
    this.bind(this.$form, 'submit', this.onSubmitForm, this);

    this.$checkDomain = dom.get('#check-domain');
    this.bind(this.$checkDomain, 'click', this.checkDomain, this);

    this.$deleteButton = dom.get('#maybe-delete');
    this.bind(this.$deleteButton, 'click', this.maybeDelete, this);

    this.$primaryColorInput = dom.get('#primary-color-input');
    this.$primaryColorLabel = dom.get('#primary-color-label');
    this.bind(this.$primaryColorInput, 'input', this.onPrimaryColorChange, this);

    this.$iconUpload = dom.get('#icon-upload');
    this.$iconDisplay = dom.get('#icon-display');
    this.iconId = this.$iconDisplay.getData('id');
    new uploadui.WebsiteIconFileChooser(this.$iconUpload, function(image) {
      this.iconId = image['id'];

      this.$iconDisplay.get('img').element.src = image['imageUrls']['full'];
      this.$iconUpload.addClass('hidden');
      this.$iconDisplay.removeClass('hidden');
    }, this);
    this.bind(dom.get('#icon-remove'), 'click', function(evt) {
      this.iconId = '';
      this.$iconUpload.removeClass('hidden');
      this.$iconDisplay.addClass('hidden');
    }, this);

    this.$logoUpload = dom.get('#logo-upload');
    this.$logoDisplay = dom.get('#logo-display');
    this.logoId = this.$logoDisplay.getData('id');
    new uploadui.WebsiteLogoFileChooser(this.$logoUpload, function(image) {
      this.logoId = image['id'];

      this.$logoDisplay.get('img').element.src = image['imageUrls']['full'];
      this.$logoUpload.addClass('hidden');
      this.$logoDisplay.removeClass('hidden');
    }, this);
    this.bind(dom.get('#logo-remove'), 'click', function(evt) {
      this.logoId = '';
      this.$logoUpload.removeClass('hidden');
      this.$logoDisplay.addClass('hidden');
    }, this);

    this.$backgroundUpload = dom.get('#background-upload');
    this.$backgroundDisplay = dom.get('#background-display');
    this.backgroundId = this.$backgroundDisplay.getData('id');
    new uploadui.WebsiteBackgroundFileChooser(this.$backgroundUpload, function(image) {
      this.backgroundId = image['id'];

      this.$backgroundDisplay.get('img').element.src = image['imageUrls']['full'];
      this.$backgroundUpload.addClass('hidden');
      this.$backgroundDisplay.removeClass('hidden');
    }, this);
    this.bind(dom.get('#background-remove'), 'click', function(evt) {
      this.backgroundId = '';
      this.$backgroundUpload.removeClass('hidden');
      this.$backgroundDisplay.addClass('hidden');
    }, this);

    var uploaders = dom.find('.screenshot-upload');
    iter.forEach(uploaders, function($uploader) {
      var platform = $uploader.getData('platform');
      new uploadui.WebsiteScreenshotFileChooser($uploader, function(image) {
        // this is to facilitate rendering.
        image.platform = platform;
        image.url = image['imageUrls']['full'];
        var thumbHtml = screenshotHtml(image);

        var $screenshotDisplay = dom.get('#screenshot-thumbs-' + platform);
        $uploader.remove();
        $screenshotDisplay.append(thumbHtml);
        $screenshotDisplay.append($uploader);
      }, this);
    }, this);

    // TODO: Review/Move/Rewrite this.
    // When tabs are selected, add hash to URL
    // When page is loaded, open tab in URL hash
    var hash = window.location.hash;
    hash && $('ul.nav a[href="' + hash + '"]').tab('show');
    $('.nav-tabs a').click(function (e) {
      $(this).tab('show');
      var scrollmem = $('body').scrollTop();
      window.location.hash = this.hash;
      $('html,body').scrollTop(scrollmem);
    });

    this.initialForm = this.$form.serializeForm();
    window.onbeforeunload = function() {
      var latestForm = this.$form.serializeForm();

      for (var k in this.initialForm) {
        if (this.initialForm[k] != latestForm[k]) {
          this.unsavedChanges = true;
        }
      }

      if (this.unsavedChanges == true && this.initialForm) {
        return 'You have unsaved changes, do you still want to leave this page?';
      }
    }.bind(this)
  },

  onPrimaryColorChange: function() {
    var primaryColor = colors.humanInputToHex(this.$primaryColorInput.value());
    if (!primaryColor) {
      return;
    }

    this.$primaryColorLabel.element.style.backgroundColor = primaryColor;
  },

  showErrors: function(errors) {
    for (var fieldName in errors) {
      var field = dom.get('[name=' + fieldName + ']');
      if (field) {
        // TODO(Taylor,Lance): Make sure this tab is focused!
        field.addClass('has-error');
      }
    }
    showErrorMessage();
  },

  checkDomain: function(evt) {
    if (this.checking) {
      return;
    }
    this.checking = true;

    var $successBox = dom.get('#check-domain-good');
    var $errorBox = dom.get('#check-domain-bad');
    $successBox.addClass('hidden');
    $errorBox.addClass('hidden');

    var domain = dom.get('#domain-input').value();
    LKAPIClient.checkDomainCname(domain, {
      onSuccess: function(correct, error) {
        if (correct) {
          $successBox.removeClass('hidden');
        } else {
          $errorBox.removeClass('hidden');
          $errorBox.get('.sub-message').setText(error || 'An unknown error occurred.');
        }
      },
      onComplete: function() {
        this.checking = false;
      },
      context: this
    });
  },

  onSubmitForm: function(evt) {
    evt.preventDefault();

    var errors = dom.find('.has-error');
    iter.forEach(errors, function(error) {
      error.removeClass('has-error');
    });

    var formData = this.$form.serializeForm();

    if (formData['primary_color'] !== '') {
      var primaryColor = colors.humanInputToHex(formData['primary_color']);
      if (!primaryColor) {
        this.showErrors({'primary_color': ['Enter a valid value.']});
        return;
      }
      formData['primary_color'] = primaryColor;
    }

    formData['icon_id'] = this.iconId;
    formData['logo_id'] = this.logoId;
    formData['background_id'] = this.backgroundId;

    var screenshotImagesIds = iter.map(dom.find('.screenshot-thumb[data-platform=iPhone]'), function($s) {
      return $s.getData('image-id');
    });
    formData['iphone_screenshot_ids'] = screenshotImagesIds.join(',');

    LKAPIClient.editWebsite(this.website['id'], formData, {
      onSuccess: function(website) {
        delete this.initialForm;
        navigation.navigate('/websites/dashboard/?saved=1');
      },
      onError: function(code, data) {
        if (code === 400) {
          this.showErrors(data.errors);
        }
      },
      context: this
    });
  },

  maybeDelete: function(evt) {
    showDeleteMessage.call(this);
  },

  handleAction: function(action, $target) {
    Dashboard.prototype.handleAction.apply(this, arguments);

    var move = 0;
    switch (action) {
      case 'screenshot-left':
        move = -1;
      case 'screenshot-right':
        move = move || 1;

      case 'screenshot-remove':
        var $thumb = $target.up('.screenshot-thumb');
        var $parent = $thumb.parent();
        var $children = $parent.children();
        var index = iter.indexOf($children, function($c) { return $c.element == $thumb.element });
        $thumb.remove();
        $children.splice(index, 1);

        if (move) {
          var $before = $children[index + move];
          if ($before) {
            $parent.element.insertBefore($thumb.element, $before.element);
          } else {
            $parent.append($thumb);
          }
        }
        break;

      case 'preview-page':
        var page_content = document.getElementById($target.getData('page')).value;

        if (!page_content.length) {
          var okay = new ButtonOverlay('Whoops!', 'Please provide some content to preview.');
          okay.addButton('Okay');
          okay.show();
        } else {
          var preview = new TitledOverlay('Content', {
            content: markdown(page_content)
          })
          preview.show();
        }
        break;

    }

  }

});
