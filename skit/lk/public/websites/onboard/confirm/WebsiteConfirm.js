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
var object = skit.platform.object;
var util = skit.platform.util;
var urls = skit.platform.urls;

var LKAPIClient = library.api.LKAPIClient;
var Dashboard = library.controllers.Dashboard;
var ButtonOverlay = library.overlays.ButtonOverlay;
var colors = library.misc.colors;
var fonts = library.screenshots.fonts;
var uploadui = library.screenshots.uploadui;
var ColorThief = third_party.ColorThief;

var html = __module__.html;


var showErrorMessage = function() {
  var okay = new ButtonOverlay('Whoops!', 'There are some errors with the input, please correct the red fields.');
  okay.addButton('Okay');
  okay.show();
};


module.exports = Controller.create(Dashboard, {
  enableLoggedOut: true,

  __preload__: function(done) {
    var query = navigation.query();
    this.itunesId = query['itunesId'];
    this.country = query['country'];

    LKAPIClient.getExampleWebsite(this.itunesId, this.country, {
      onSuccess: function(website) {
        this.website = website;

        if (query['template']) {
          this.website['template'] = query['template'];
        }
      },
      onError: function() {
        navigation.notFound();
      },
      onComplete: function() {
        done();
      },
      context: this
    });
  },

  __title__: function() {
    return 'Edit ' + this.website['appName'] + ' Website';
  },

  __body__: function() {

    return {
      content: html({
        'fonts': fonts.FONTS,
        'website': this.website
      })
    };
  },

  __ready__: function() {
    this.$form = dom.get('#app-website-confirm-form');
    this.bind(this.$form, 'submit', this.onSubmitForm, this);

    this.$primaryColorInput = dom.get('#primary-color-input');
    this.$primaryColorLabel = dom.get('#primary-color-label');
    this.bind(this.$primaryColorInput, 'input', this.onPrimaryColorChange, this);

    var ct = new ColorThief();
    var image = new Image();
    image.crossOrigin = 'Anonymous';
    image.onload = util.bind(function() {
      var color = colors.rgbToHex(ct.getPalette(image, 6)[0]);
      this.$primaryColorInput.setValue(color);
      this.$primaryColorLabel.element.style.backgroundColor = color;
    }, this);
    image.src = this.website.images.icon.url;
  },

  onPrimaryColorChange: function() {
    var primaryColor = colors.humanInputToHex(this.$primaryColorInput.value());
    if(!primaryColor) {
      return;
    }

    this.$primaryColorLabel.element.style.backgroundColor = primaryColor;
  },

  showErrors: function(errors) {
    iter.forEach(Object.keys(errors), function(field) {
      dom.get('input[name=' + field + ']').addClass('has-error');
    });
    showErrorMessage();
  },

  onSubmitForm: function(evt) {
    evt.preventDefault();

    var errors = dom.find('.has-error');
    if(errors.length > 0) {
      iter.forEach(errors, function(error) {
        error.removeClass('has-error');
      });
    }

    var formData = this.$form.serializeForm();

    if (formData['primary_color']) {
      var primaryColor = colors.humanInputToHex(formData['primary_color']);
      if(!primaryColor) {
        this.showErrors({'primary_color': ['Enter a valid value.']});
        return;
      }
      formData['primary_color'] = primaryColor;
    }

    var params = object.copy(formData);
    params['itunesId'] = this.itunesId;
    params['country'] = this.country;
    navigation.navigate(urls.appendParams('/websites/dashboard/example/templates/', params));
  }

});
