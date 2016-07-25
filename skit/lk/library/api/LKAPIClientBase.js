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

var PubSub = skit.platform.PubSub;
var net = skit.platform.net;
var netproxy = skit.platform.netproxy;
var urls = skit.platform.urls;
var iter = skit.platform.iter;
var util = skit.platform.util;


function LKAPIClientBase() {}


LKAPIClientBase.prototype.TOKEN_INVALIDATED_NOTIFICATION = 'LKAPIClientBase:token-invalidated';
LKAPIClientBase.prototype.SITE_READONLY_NOTIFICATION = 'LKAPIClientBase:site-readonly';


LKAPIClientBase.prototype.currentUser = null;


LKAPIClientBase.prototype.setCurrentUser = function(currentUser) {
  this.currentUser = currentUser;
};


LKAPIClientBase.prototype.currentUserId = function() {
  return this.currentUser && this.currentUser['id'];
};


LKAPIClientBase.prototype.send_ = function(path, options) {
  var handleResponse = function(response) {
    var allCallbacks = options.callbacks || {};
    if (!allCallbacks.length) {
      allCallbacks = [allCallbacks];
    }

    var data = response.body;
    var parsed;
    var success = false;
    if (response.status == 200) {
      success = true;
      parsed = (options.parse || function(d) { return [d]; }).call(this, data);
    } else if (response.status == 401) {
      PubSub.sharedPubSub().publish(this.TOKEN_INVALIDATED_NOTIFICATION);
      parsed = [];
    } else if (response.status == 503) {
      PubSub.sharedPubSub().publish(this.SITE_READONLY_NOTIFICATION);
      parsed = [];
    } else {
      parsed = [];
    }

    iter.forEach(allCallbacks, function(callbacks) {
      if (!callbacks) {
        return;
      }

      if (success) {
        if (callbacks.onSuccess) {
          callbacks.onSuccess.apply(callbacks.context, parsed);
        }
      } else {
        if (callbacks.onError) {
          callbacks.onError.call(callbacks.context, response.status, data);
        }
      }

      if (callbacks.onComplete) {
        callbacks.onComplete.apply(callbacks.context, parsed);
      }
    }, this);
  };

  // This wraps normal .net operations to proxy through the local server
  // so we can save some details client-side.
  var proxy = netproxy.getProxyNamed('lk');

  if (options.json) {
    net.send(path, {
      proxy: proxy,
      method: options.method,
      body: JSON.stringify(options.json),
      headers: {'Content-Type': 'application/json'},
      complete: util.bind(handleResponse, this)
    });

  } else {
    var params;
    if (options.params) {
      if (typeof options.params == 'string') {
        params = options.params;
      } else {
        params = {};
        var value;
        for (var k in options.params) {
          value = options.params[k];
          if (value !== undefined && value !== null) {
            params[k] = value;
          }
        }
      }
    }

    net.send(path, {
      proxy: proxy,
      method: options.method,
      params: params,
      complete: util.bind(handleResponse, this)
    });
  }
};


module.exports = LKAPIClientBase;
