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
var Controller = skit.platform.Controller;
var PubSub = skit.platform.PubSub;
var cookies = skit.platform.cookies;
var iter = skit.platform.iter;
var navigation = skit.platform.navigation;
var urls = skit.platform.urls;
var util = skit.platform.util;
var Handlebars = skit.thirdparty.handlebars;

var LKAPIClient = library.api.LKAPIClient;
var products = library.products.products;
var googleanalytics = library.misc.googleanalytics;
var useragent = library.misc.useragent;
var scripts = library.misc.scripts;
var templatehelpers = library.misc.templatehelpers;
// Included for all pages.
var bootstrap = library.misc.bootstrap;
var fontawesome = library.misc.fontawesome;

var html = __module__.html;
var meta = __module__.meta.html;


// TODO: Set your analytics ID.
var GA_ID = 'UA-XXXXXXXX-1';

// Global template helpers
templatehelpers.registerAll();


module.exports = Controller.create({
  showHelpButton: false,
  dontLoadUser: false,
  gaId: GA_ID,

  __preload__: function(done) {
    this.user = null;
    this.wireUpClientSideHack();

    // No use looking this up if the cookie is not present.
    if (!cookies.get('lkauth') || this.dontLoadUser) {
      done();
      return;
    }

    LKAPIClient.user({
      onSuccess: function(me) {
        this.user = me;

        // update this.user in LKAPIClient.
        this.wireUpClientSideHack();
      },
      onComplete: done,
      context: this
    });
  },

  wireUpClientSideHack: function() {
    // This is a slight hack to fix client-side initial load of user object.
    LKAPIClient.setCurrentUser(this.user);
    // This must be done after setting this.products.
    this.product = products.findByUrl(navigation.url());
  },

  reloadWithUser: function() {
    LKAPIClient.user({
      onSuccess: function(me) {
        this.user = me;
        // update this.user in LKAPIClient.
        this.wireUpClientSideHack();
      },
      onComplete: function() {
        this.reload();
      },
      context: this
    });
  },

  __load__: function() {
    this.wireUpClientSideHack();
  },

  __title__: function(childTitle) {
    return childTitle;
  },

  __meta__: function(childMeta) {
    return childMeta + meta();
  },

  __body__: function(childHtml) {
    return html({
      childHtml: childHtml,
      showHelp: this.showHelpButton
    });
  },

  isDevelopment: function() {
    var parsed = urls.parse(window.location.href);
    return parsed.port && parsed.port != 80 && parsed.port != 443;
  },

  redirectUrl: function(opt_default) {
    var query = navigation.query();
    var redirect = query['redirect'] || query['next'];

    if (redirect && redirect.indexOf('/') == 0) {
      return redirect;
    }
    return opt_default || '/';
  },

  __ready__: function() {
    this.baseListeners_ = [];
    this.baseSubscriptions_ = [];

    // ontouchstart is null in mobilesafari, but undefined in other browsers.
    if (useragent.isMobile() && document.body.ontouchstart !== undefined) {
      // In the event that
      this.delegate(document.body, '[data-action]', 'touchstart', function(touchstartEvent) {
        var target = touchstartEvent.target;
        var currentTarget = touchstartEvent.currentTarget;
        var moved = false;
        var leaveid = events.bind(target, 'touchmove', function(touchLeaveEvent) {
          moved = true;
        });
        var endid = events.bind(target, 'touchend', function(touchendEvent) {
          if (!moved) {
            touchendEvent.currentTarget = currentTarget;
            this.onClickAction(touchendEvent);
          }
          // do this here, not in 'touchmove', in case the touch never moves.
          events.unbind(leaveid);
          events.unbind(endid);
        }, this);
      }, this);
    } else {
      // Just use click handlers.
      this.delegate(document.body, '[data-action]', 'click', this.onClickAction, this);
    }

    if (this.isDevelopment()) {
      return;
    }

    util.setTimeout(function() {
      // Google Analytics.
      googleanalytics.create(this.gaId);
      googleanalytics.trackPageview();
    }, 100, this);
  },

  __unload__: function() {
    var listeners = this.baseListeners_;
    this.baseListeners_ = [];
    iter.forEach(listeners, function(listener) {
      events.unbind(listener);
    });

    var subs = this.baseSubscriptions_;
    var pubsub = PubSub.sharedPubSub();
    this.baseSubscriptions_ = [];
    iter.forEach(subs, function(sub) {
      pubsub.unsubscribe(sub);
    });
  },

  bind: function() {
    this.baseListeners_.push(events.bind.apply(events, arguments));
  },
  delegate: function() {
    this.baseListeners_.push(events.delegate.apply(events, arguments));
  },
  subscribe: function() {
    var pubsub = PubSub.sharedPubSub();
    this.baseSubscriptions_.push(pubsub.subscribe.apply(pubsub, arguments));
  },

  onClickAction: function(evt) {
    evt.preventDefault();
    var name = evt.currentTarget.getData('action');
    this.handleAction(name, evt.currentTarget);
  },

  handleAction: function(name, $target) {
  }
});
