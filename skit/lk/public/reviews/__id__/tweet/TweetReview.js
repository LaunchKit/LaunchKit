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

var AmbiguousProgressOverlay = library.overlays.AmbiguousProgressOverlay;
var ButtonOverlay = library.overlays.ButtonOverlay;
var LKAPIClient = library.api.LKAPIClient;
var Dashboard = library.controllers.Dashboard;

var html = __module__.html;
var twitterText = third_party.twitterText;


function isInvalidTweet(text) {
  isInvalid = twitterText.isInvalidTweet(text);
  if(!isInvalid) {
    if(twitterText.getTweetLength(text) > 140 - 23) {
      return 'too_long';
    } else {
      return false;
    }
  }

  return isInvalid;
}


function showMessage(error) {
  var message;
  var title = 'Whoops!';
  if(!error) {
    title = 'Yay!';
    message = 'Your tweet has been posted!';
  }
  else if(error == 'too_long') {
    message = "The tweet text entered is too long. Please limit text to 110 characters.";
  }
  else if(error == 'invalid_characters') {
    message = 'The tweet entered contains characters which are invalid.'
  }
  else if(error == 'empty') {
    message = 'Please enter some text to tweet.'
  }
  else {
    message = 'Sorry, but we had a problem tweeting this for you. Please try again later, or use the link below to just tweet it now.';
  }

  var okay = new ButtonOverlay(title, message);
  okay.addButton('Okay');
  okay.show();
}


module.exports = Controller.create(Dashboard, {
  __preload__: function(done) {
    var reviewId = this.params['__id__'];
    if (!/^[\w-]{11}$/.test(reviewId)) {
      navigation.notFound();
      done();
      return;
    }

    var i = 2;
    function maybeFinish() {
      i--;
      if(i != 0) {
        return;
      }

      var connection = iter.find(this.connections, function(c) {
        return c.app.id == this.review.appId;
      }, this);

      if(connection) {
        this.twitterHandle = connection.twitterHandle;
      }

      done();
    }

    LKAPIClient.review(reviewId, {
      onSuccess: function(review) {
        this.review = review;
      },
      onError: function() {
        navigation.notFound();
        done();
      },
      onComplete: maybeFinish,
      context: this
    });

    LKAPIClient.twitterAppConnections({
      onSuccess: function(connections, _, _) {
        this.connections = connections;
      },
      onComplete: maybeFinish,
      context: this
    });
  },

  __title__: function() {
    return 'Tweet Review'
  },

  __body__: function() {
    return {
      content: html({
        review: this.review,
        twitterHandle: this.twitterHandle
      })
    };
  },

  __ready__: function() {
    setTimeout(function() {
      var script = document.createElement('script');
      script.id = 'twitter-wjs';
      script.src = '//platform.twitter.com/widgets.js';
      document.getElementsByTagName('head')[0].appendChild(script);
    }, 0);
  },

  handleAction: function(type, $target) {
    Dashboard.prototype.handleAction.apply(this, arguments);

    switch(type) {
      case 'tweet':
        if(this.tweeting) {
          return;
        }
        this.tweeting = true;

        var tweetText = dom.get('#tweet-text').value().trim();
        var isInvalid = isInvalidTweet(tweetText);
        if (isInvalid) {
          showMessage(isInvalid);
        } else {
          var progress = new AmbiguousProgressOverlay('Tweeting...');
          progress.show();

          var twitterHandle = $target.getData('twitterHandle');
          var reviewId = $target.getData('reviewId');

          LKAPIClient.tweetReview(twitterHandle, reviewId, tweetText, {
            onSuccess: function() {
              showMessage(false);
            },
            onError: function() {
              showMessage(true);
            },
            onComplete: function() {
              progress.done();
            }
          });
        }

        delete this.tweeting;

        break;
    }
  }
});
