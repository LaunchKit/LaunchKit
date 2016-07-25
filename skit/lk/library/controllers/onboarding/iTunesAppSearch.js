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
var util = skit.platform.util;

var LKAPIClient = library.api.LKAPIClient;
var Dashboard = library.controllers.Dashboard;
var ButtonOverlay = library.overlays.ButtonOverlay;
var AmbiguousProgressOverlay = library.overlays.AmbiguousProgressOverlay;
var itunessearch = library.misc.itunessearch;
var scripts = library.misc.scripts;

var navItemHtml = library.products.navitem;
var resultHtml = __module__.result.html;
var startHtml = __module__.start.html;


module.exports = Controller.create(Dashboard, {
  // TO OVERRIDE THESE:

  headlineText: '',
  subheadText: '',
  skipUrl: null,
  getResultUrl: function(result, country) {
    return '';
  },
  resultAction: null,

  // END SUBCONTROLLER OVERRIDES

  enableLoggedOut: true,

  __body__: function() {
    return {
      content: startHtml({
        headlineText: this.headlineText,
        subheadText: this.subheadText,
        skipUrl: this.skipUrl,
        countries: itunessearch.COUNTRIES
      })
    };
  },

  __ready__: function() {
    this.searchForm = dom.get('#itunes-search-form');
    if (!this.searchForm) {
      // Child controller, this confusingly behaves as a parent.
      return;
    }

    this.bind(this.searchForm, 'submit', this.onSubmitSearch, this);

    this.$country = dom.get('#itunes-country-select');
    this.bind(this.$country, 'change', this.onSubmitSearch, this);

    this.results = dom.get('#itunes-search-results');

    var $input = this.searchForm.get('input[type=text]');
    setTimeout(function() {
      $input.element.focus();
      $input.element.select();
    }, 250);

    // Hitting back, you end up here.
    if ($input.value()) {
      this.onSubmitSearch();
    }
  },

  onSubmitSearch: function(opt_evt) {
    if (opt_evt) {
      opt_evt.preventDefault();
    }

    var button = this.searchForm.get('button.btn-primary');
    if (button) {
      button.removeClass('btn-primary');
    }

    this.results.addClass('loading');
    this.results.removeChildren();

    var query = this.searchForm.get('input[type=text]').value();
    this.lastQuery = query;

    var country = this.$country.value();
    itunessearch.findApps(country, query, function(resultsQuery, results) {
      if (resultsQuery != this.lastQuery) {
        return;
      }

      var filteredResults = iter.map(results, function(result) {
        result['url'] = this.getResultUrl(result, country);
        result['action'] = this.resultAction;
      }, this);

      this.results.removeClass('loading');
      this.results.element.innerHTML = iter.map(results, function(r) {
        r.country = country;
        return resultHtml(r);
      }).join('');
    }, this, {ipad: false, mac: false});
  }
});
