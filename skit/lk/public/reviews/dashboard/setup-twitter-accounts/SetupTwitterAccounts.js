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
var Dashboard = library.controllers.Dashboard;
var LKAPIClient = library.api.LKAPIClient;

var html = __module__.html;


var NEXT_URL = '/reviews/dashboard/setup-email/';


function getTweetReviewUrl(reviewId) {
  return '/reviews/' + reviewId + '/tweet';
}

function showError() {
  var okay = new ButtonOverlay('Whoops!', 'We ran into a problem connecting with Twitter. Please try again later.');
  okay.addButton('Okay');
  okay.show();
}


module.exports = Controller.create(Dashboard, {
  __preload__: function(done) {
    var query = navigation.query();
    this.highlightApp = query['callbackApp']

    LKAPIClient.twitterAppConnections({
      onSuccess: function(connections, unconnectedApps, twitterHandles) {
        this.connections = connections;
        this.unconnectedApps = unconnectedApps;
        this.twitterHandles = twitterHandles;
      },
      onComplete: done,
      context: this
    });
  },

  __title__: function() {
    return 'Setup Twitter';
  },

  __body__: function() {
    return {
      contentClass: 'col-md-12',
      content: html({
        connections: this.connections,
        unconnectedApps: this.unconnectedApps,
        twitterHandles: this.twitterHandles,
        highlightApp: this.highlightApp,
        needsReviewsOnboarding: this.user['needsReviewsOnboarding'],
        nextUrl: NEXT_URL
      })
    };
  },

  __ready__: function() {
    var query = navigation.query();
    if(query['error']) {
      showError();
    }
  },

  handleAction: function(type, $target) {
    Dashboard.prototype.handleAction.apply(this, arguments);

    switch(type) {
      case 'add':
        this.progress = new AmbiguousProgressOverlay('Redirecting you to Twitter...');
        this.progress.show();

        var appId = $target.up('ul').getData('appId');
        var query = navigation.query();
        var callbackUrl;
        if(query['callbackApp'] == appId && query['callbackReview']) {
          callbackUrl = encodeURIComponent(getTweetReviewUrl(query['callbackReview']));
        }

        LKAPIClient.twitterConnect(appId, callbackUrl, {
          onSuccess: function(twitterConnectUrl) {
            navigation.navigate(twitterConnectUrl);
          },
          onError: function() {
            this.progress.done();
            showError();
          },
          context: this
        });
        break;
      case 'connect':
        if (this.connecting) {
          return;
        }
        this.connecting = true;

        var $li = $target.up('li');
        var appId = $li.up('ul').getData('appId');
        var twitterHandle = $li.getData('twitterHandle');

        LKAPIClient.connectAppToTwitter(appId, twitterHandle, {
          onSuccess: function() {
            var query = navigation.query();
            if(query['callbackReview'] && query['callbackApp'] == appId) {
              navigation.navigate(getTweetReviewUrl(query['callbackReview']))
            }
            else {
              LKAPIClient.autoSubscribeToReviewsWithTwitter(appId, {
                onComplete: function() {
                  this.reload();
                  delete this.connecting;
                },
                context: this
              });
            }
          },
          context: this
        });
        break;
      case 'autotweet':
        if (this.autotweet) {
          return;
        }
        this.autotweet= true;

        var autoTweet = $target.getChecked();

        var onComplete = function() {
          this.reload();
          delete this.autotweet;
        }

        if(autoTweet) {
          var connectionId = $target.getData('connectionId');
          LKAPIClient.subscribeToReviewsWithTwitter(connectionId, {
            onComplete: onComplete,
            context: this
          });
        }
        else {
          var subscriptionId = $target.getData('subscriptionId');
          LKAPIClient.removeReviewSubscription(subscriptionId, {
            onComplete: onComplete,
            context: this
          });
        }
        break;
      case 'remove':
        if (this.removing) {
          return;
        }
        this.removing = true;

        var id = $target.up('button').getData('connectionId');
        var subscriptionId = $target.up('button').getData('subscriptionId');

        var i = 2;
        var maybeFinish = function() {
          i--;
          if(i != 0) {
            return;
          }

          this.reload();
          delete this.removing;
        }

        LKAPIClient.disconnectAppFromTwitter(id, {
          onComplete: maybeFinish,
          context: this
        });

        LKAPIClient.removeReviewSubscription(subscriptionId, {
          onComplete: maybeFinish,
          context: this
        });
        break;
    }
  }
});
