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
var cookies = skit.platform.cookies;
var env = skit.platform.env;
var iter = skit.platform.iter;
var navigation = skit.platform.navigation;
var urls = skit.platform.urls;
var Handlebars = skit.thirdparty.handlebars;

var Base = library.controllers.Base;
var scripts = library.misc.scripts;
var meta = library.marketing.marketingmeta;
var billboard = library.marketing.marketingbillboard;
var body = library.marketing.marketingbody;
var templatehelpers = library.misc.templatehelpers;
var products = library.products.products;

var html = __module__.html;



Handlebars.registerHelper('otherCol', function(value, options) {
  var colSize = 5;
  if (value) {
    colSize = 12 - parseInt(value, 10);
  }
  if (colSize == 0) {
    colSize = 12;
  }
  return colSize;
});

Handlebars.registerHelper('ifShowSlider', function(opts) {
  if (navigation.query()['slider'] == '1') {
    return opts.fn();
  }
  return '';
});


module.exports = Controller.create(Base, {
  showHelpButton: false,

  __preload__: function(done) {
    if (!this.constructor.prototype.hasOwnProperty('__body__') && !this.product) {
      navigation.notFound();
    }

    done();
  },

  __meta__: function(childMeta) {
    // Inject optimizely here so we include it on homepage as well.
    if (!env.get('debug')) {
      childMeta += '\n<script src="//cdn.optimizely.com/js/5016490019.js"></script>\n';
    }

    if (!this.product) {
      return childMeta;
    }

    return childMeta + meta({
      product: this.product
    });
  },

  __title__: function(childTitle) {
    if (childTitle) {
      return childTitle;
    }
    if (this.product) {
      return this.product.name + ' - ' + this.product.tagline;
    }
    return '';
  },

  __body__: function(childHtml) {
    return html({
      user: this.user,
      product: this.product,
      publicProducts: products.publicProducts(),
      homepage: childHtml.homepage ? childHtml.homepage : false,
      billboard: childHtml.billboard ? childHtml.billboard : billboard({product: this.product}),
      body: childHtml.body ? childHtml.body : (childHtml ? childHtml : body({product: this.product}))
    });
  },

  __ready__: function() {
    var containers = dom.find('.pricing-container');
    iter.forEach(containers, function(container) {
      var $slider = container.get('.pricing-slider');
      var $amount = container.get('.pricing-amount');
      var updateAmount = function() {
        this.updateAmount($slider, $amount);
      };
      this.bind($slider, 'input', updateAmount, this);
      this.bind($slider, 'change', updateAmount, this);
      updateAmount.call(this);
    }, this);
  },

  updateAmount: function($slider, $amount) {
    var count = +($slider.value());
    var amount = '<span class="plan-price-users pull-left" style="color: #333;">' + templatehelpers.formatNumber(count, 0) + ' MAUs</span>';
    if (count <= 10000) {
      amount += '<span class="plan-price-dollars pull-right">FREE!</span>';
    } else if (count >= 1000000) {
      amount += '<span class="plan-price-dollars pull-right">Contact Us!</span>';
    } else {
      var dollars = templatehelpers.formatCurrency((count - 10000) / 1000.0, 2);
      amount += '<span class="plan-price-dollars pull-right">' + dollars + ' / mo.</span>';
    }
    $amount.element.innerHTML = amount;
  }
});
