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

var Controller = skit.platform.Controller;
var navigation = skit.platform.navigation;

var LKAPIClient = library.api.LKAPIClient;
var Base = library.controllers.Base;

var html = __module__.html;
var meta = __module__.meta.html;


module.exports = Controller.create(Base, {
  __preload__: function(done) {
    var reviewId = this.params['__id__'];
    if (!/^[\w-]{11}$/.test(reviewId)) {
      navigation.notFound();
      done();
      return;
    }

    LKAPIClient.review(reviewId, {
      onSuccess: function(review) {
        this.review = review;
      },
      onError: function() {
        navigation.notFound();
      },
      onComplete: done,
      context: this
    });
  },

  __title__: function() {
    return this.review.rating + ' star review for ' +
        this.review.app.names.short + ': ' + this.review.title;
  },

  __meta__: function() {
    return meta({
      review: this.review
    });
  },

  __body__: function() {
    return html({
      review: this.review
    });
  },

  __ready__: function() {
    setTimeout(function() {
      var script = document.createElement('script');
      script.id = 'twitter-wjs';
      script.src = '//platform.twitter.com/widgets.js';
      document.getElementsByTagName('head')[0].appendChild(script);
    }, 0);
  }
});
