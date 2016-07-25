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
var urls = skit.platform.urls;

var LKAPIClient = library.api.LKAPIClient;
var Dashboard = library.controllers.Dashboard;

var html = __module__.html;
var errorHtml = __module__.error.html;
var invalidTokenHtml = __module__.invalid_token.html;
var channelsHtml = __module__.channels.html;


var STATE_MISMATCH = 'state_mismatch';
var NO_CODE = 'no_code';
var NO_SERVICE = 'no_service';
var BACKEND_ERROR = 'backend_error';


var SERVICES = {
  reviews: {
    name: 'reviews',
    url: '/reviews/dashboard/'
  },
  sales: {
    name: 'sales reports',
    url: '/sales/dashboard/'
  }
};


module.exports = Controller.create(Dashboard, {
  __preload__: function(loaded) {
    if (!this.user) {
      var loginUrl = urls.appendParams('/login/', {'redirect': navigation.relativeUrl()});
      navigation.navigate(loginUrl);
      loaded();
      return;
    }

    var query = navigation.query();
    this.service = SERVICES[query['service']];
    this.onboarding = !!query['onboarding'];

    if (query['error']) {
      this.error = query['error'];
      loaded();
      return;
    }

    if (!query['service'] || !SERVICES[query['service']]) {
      this.error = NO_SERVICE;
      loaded();
      return;
    }

    LKAPIClient.slackChannels({
      onSuccess: function(tokenValid, channels) {
        this.tokenValid = tokenValid;
        this.channels = channels || [];

        if (this.channels.length == 1 && this.onboarding) {
          this.finishWithChannelName(this.channels[0]['name'], loaded);
        } else {
          loaded();
        }
      },
      onError: function(status) {
        if (status != 400) {
          this.error = BACKEND_ERROR;
          loaded();
          return;
        }

        this.navigateToSlackAuth();
        loaded();
      },
      context: this
    });
  },

  __title__: function() {
    return 'Connect Slack';
  },

  __body__: function() {
    var disconnectUrl = urls.appendParams('/account/slack/disconnect/', {'redirect': navigation.relativeUrl()});
    var content;
    if (this.error) {
      content = errorHtml({
        service: this.service,
        error: this.error
      });

    } else if (!this.tokenValid) {
      content = invalidTokenHtml({
        service: this.service,
        disconnectUrl: disconnectUrl
      });

    } else {
      content = channelsHtml({
        channels: this.channels,
        service: this.service,
        disconnectUrl: disconnectUrl
      });
    }

    return {
      content: html({
        contentHtml: content
      })
    };
  },

  __ready__: function() {
    this.delegate(document.body, '[data-select-channel]', 'click', this.onClickChannel, this);
    this.delegate(document.body, '[data-reauthorize]', 'click', function(e) {
      e.preventDefault();
      this.navigateToSlackAuth();
    }, this);
  },

  navigateToSlackAuth: function() {
    var expectedState = this.user['createTime'];

    var parsed = urls.parse(navigation.url());
    var baseUrl = parsed.scheme + '://' + parsed.host + '/account/slack/finish/';

    var finishUrl = urls.appendParams(baseUrl, parsed.params);
    var authorizationUrl = urls.appendParams('https://slack.com/oauth/authorize', {
      'scope': 'incoming-webhook',
      'client_id': '2225851159.3605239197',
      'redirect_uri': finishUrl,
      'state': expectedState
    });

    navigation.navigate(authorizationUrl);
  },

  finishWithChannelName: function(channelName, opt_loaded) {
    function done() {
      var redirectUrl = this.service.url;
      if (this.onboarding) {
        redirectUrl += 'setup-slack-yay/';
      }

      navigation.navigate(redirectUrl);
      opt_loaded && opt_loaded();
    }

    if (this.service.name == SERVICES.reviews.name) {
      LKAPIClient.subscribeToReviewsWithSlackChannel(channelName, {
        onComplete: done,
        context: this
      });
    } else if (this.service.name == SERVICES.sales.name) {
      LKAPIClient.subscribeToSalesReportsWithSlackChannel(channelName, {
        onComplete: done,
        context: this
      });
    }
  },

  onClickChannel: function(evt) {
    evt.preventDefault();

    if (this.selecting) {
      return;
    }
    this.selecting = true;

    dom.get('.slack-connect').addClass('loading');

    var channelName = evt.currentTarget.getData('channel-name') || null;
    this.finishWithChannelName(channelName);
  }
});
