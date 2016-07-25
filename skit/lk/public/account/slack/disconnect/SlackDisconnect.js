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

var LKAPIClient = library.api.LKAPIClient;
var FloatingBox = library.controllers.FloatingBox;

var html = __module__.html;



module.exports = Controller.create(FloatingBox, {
  __preload__: function(loaded) {
    LKAPIClient.slackUsage({
      onSuccess: function(connected, channelsByProduct) {
        this.connected = connected;
        this.channelsByProduct = channelsByProduct;
      },
      onComplete: loaded,
      context: this
    });
  },

  __body__: function() {
    var backUrl = this.redirectUrl();

    return html({
      connected: this.connected,
      channelsByProduct: this.channelsByProduct,
      backUrl: backUrl
    });
  },

  __title__: function() {
    return 'Disconnect Slack';
  },

  handleAction: function(action, $target) {
    FloatingBox.prototype.handleAction.call(this, action, $target);

    switch (action) {
      case 'disconnect-slack':
        this.disconnectSlack_($target);
        break;
    }
  },

  disconnectSlack_: function($button) {
    $button.disable();

    LKAPIClient.slackDisconnect({
      onComplete: function() {
        this.reload();
      },
      context: this
    });
  }
});
