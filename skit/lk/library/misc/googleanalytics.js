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

var scripts = library.misc.scripts;

var loaded = false;


function getGA_() {
  var ga = window['ga'] = window['ga'] || function() {
    ga['q'] = ga['q'] || [];
    ga['q'].push(arguments);
  };
  ga['l'] = 1 * (new Date());
  return ga;
}


function create(trackingId, opt_name) {
  var ga = getGA_();
  var name = opt_name || 'auto';

  ga('create', trackingId, opt_name ? {'name': opt_name} : undefined);

  if (!loaded) {
    scripts.load('https://www.google-analytics.com/analytics.js');
    loaded = true;
  }
}

function trackPageview(opt_name) {
  var ga = getGA_();
  ga(opt_name ? opt_name + '.send' : 'send', 'pageview');
}


//
// OPTIONS:
//
// Field Name      Type     Required  Description
// eventCategory   text     yes       Typically the object that was interacted with (e.g. 'Video')
// eventAction     text     yes       The type of interaction (e.g. 'play')
// eventLabel      text     no        Useful for categorizing events (e.g. 'Fall Campaign')
// eventValue      integer  no        A numeric value associated with the event (e.g. 42)
//
function trackEvent(options, opt_name) {
  var ga = getGA_();

  var params = {'hitType': 'event'};
  for (var k in options) {
    params[k] = options[k];
  }

  ga(opt_name ? opt_name + '.send' : 'send', params);
}


function set(dimension, value, opt_name) {
  var ga = getGA_();
  ga(opt_name ? opt_name + '.set' : 'set', dimension, value);
}


module.exports = {
  create: create,
  trackPageview: trackPageview,
  trackEvent: trackEvent,
  set: set
};