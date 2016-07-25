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
var urls = skit.platform.urls;
var Handlebars = skit.thirdparty.handlebars;

var Dashboard = library.controllers.Dashboard;
var LKAPIClient = library.api.LKAPIClient;
var introHtml = library.products.dashboardintro;

var html = __module__.html;
var nuxHtml = __module__.nux.html;
var sidebarHtml = __module__.sidebar.html;

var messageWrapperHtml = __module__.message.html;
var messageEmptyHtml = __module__.message_empty.html;
var messageFailedHtml = __module__.message_failed.html;
var messageUnavailableHtml = __module__.message_unavailable.html;
var messagePendingHtml = __module__.message_pending.html;


var DAY_MS = 60 * 60 * 24 * 1000;

Handlebars.registerHelper('formattedDelta', function(metric) {
  var classTag = null;
  var deltaSymbol = '';

  if (!metric) {
    return Handlebars.SafeString('<span>N/A</span>');
  }
  if (metric > 0) {
    classTag = ' class="positive"';
    deltaSymbol = '\u25B2 ';
  } else if (metric < 0) {
    classTag = ' class="negative"';
    deltaSymbol = '\u25BC ';
  }
  var html = '<span' + classTag + '>' + deltaSymbol + metric + '%</span>';
  return new Handlebars.SafeString(html);
});

module.exports = Controller.create(Dashboard, {
  __preload__: function(loaded) {
    var i = 2;
    var maybeFinish = function() {
      i--;
      if (i != 0) {
        return;
      }

      // this.vendor indicates that we have set up an account here before.
      if (this.vendor && this.user['needsSalesOnboarding']) {
        navigation.navigate('/sales/dashboard/setup-slack/');
      }

      loaded();
    };

    var query = navigation.query();
    var queryDate = null;
    if (query['date']) {
      var timestamp = +(query['date']);
      if (timestamp % DAY_MS === 0) {
        queryDate = new Date(timestamp);
      }
    }

    LKAPIClient.salesMetrics(queryDate, {
      onSuccess: function(d) {
        this.status = d.status;
        this.vendor = d.vendor;
        this.date = d.date * 1000.0;

        // These might be null.
        this.appSalesMetrics = d.appSalesMetrics;
        this.totalSalesMetrics = d.totalSalesMetrics;
      },
      onError: function(code, body) {
        if (code >= 500) {
          throw new Error('Service unavailable: ' + body);
        }
      },
      onComplete: maybeFinish,
      context: this
    });

    LKAPIClient.salesReportSubscriptions({
      onSuccess: function(subscriptions) {
        this.subscriptions = subscriptions;
      },
      onComplete: maybeFinish,
      context: this
    });
  },

  __load__: function() {
    this.date = new Date(this.date);
  },

  __title__: function() {
    return this.product.name + ' Dashboard';
  },

  previousUrl: function() {
    if (this.status == 'unavailable') {
      return null;
    }

    var previousDate = new Date((+this.date) - DAY_MS);
    return urls.appendParams(navigation.relativeUrl(), {'date': +previousDate});
  },
  nextUrl: function() {
    // the 5/16 report is actually 5/17 at 00:00 because 5/17 is the end time.
    var TODAY_REPORT_MS = +(new Date());
    TODAY_REPORT_MS -= TODAY_REPORT_MS % DAY_MS;
    TODAY_REPORT_MS -= DAY_MS;

    var YESTERDAY_REPORT_MS = TODAY_REPORT_MS - DAY_MS;
    if (+this.date > YESTERDAY_REPORT_MS) {
      return null;
    }

    var nextDate = new Date(+(this.date) + DAY_MS);
    return urls.appendParams(navigation.relativeUrl(), {'date': +nextDate});
  },

  __body__: function() {
    // HAS NOT SET UP SALES MONITOR YET
    if (!this.vendor) {
      return {
        content: introHtml({product: this.product})
      };
    }

    // HAS NOT BEEN INGESTED YET
    // TODO(keith) - check if need onboarding and send to onboarding if so.
    var userHasPending = !this.user['salesReportReady'];
    var showNux = userHasPending || navigation.query()['nux'] == '1';
    if (showNux) {
      return {
        content: nuxHtml()
      };
    }

    var myEmailSubscription;
    var emailSubscriptions = [];
    var slackSubscription;
    iter.forEach(this.subscriptions, function(sub) {
      if (sub['myEmail']) {
        myEmailSubscription = sub;
      } else if (sub['email']) {
        emailSubscriptions.push(sub);
      } else if (sub['slackChannel']) {
        slackSubscription = sub;
      } else if (sub['slackUrl']) {
        slackSubscription = sub;
      }
    });

    var templateParams = {
      date: this.date,
      previousUrl: this.previousUrl(),
      nextUrl: this.nextUrl(),
      slackSubscription: slackSubscription,
      emailSubscriptions: emailSubscriptions,
      myEmailSubscription: myEmailSubscription,
      hasEmailSubscription: myEmailSubscription || emailSubscriptions.length > 0,
      vendor: this.vendor,
      user: this.user
    };

    var contentHtml;
    templateParams.appSalesMetrics = this.appSalesMetrics;
    templateParams.totalSalesMetrics = this.totalSalesMetrics;

    contentHtml = html(templateParams);
    if (this.status == 'available') {
      templateParams.appSalesMetrics = this.appSalesMetrics;
      templateParams.totalSalesMetrics = this.totalSalesMetrics;

      contentHtml = html(templateParams);
    } else {
      var message;
      if (this.status == 'unavailable') {
        message = messageUnavailableHtml();
      } else if (this.status == 'failed') {
        message = messageFailedHtml();
      } else if (this.status == 'pending') {
        message = messagePendingHtml();
      } else if (this.status == 'empty') {
        message = messageEmptyHtml();
      } else {
        throw new Error('Unknown status: ' + this.status);
      }

      templateParams.messageHtml = message;
      contentHtml = messageWrapperHtml(templateParams);
    }

    return {
      content: contentHtml
    };
  },

  __ready__: function() {
    var emailForm = dom.get('#email-add-form');
    if (emailForm) {
      this.bind(emailForm, 'submit', this.onSubmitEmail, this);
    }
  },

  handleAction: function(action, $target) {
    Dashboard.prototype.handleAction.apply(this, arguments);

    switch(action) {
      case 'remove-subscription':
        this.removeSubscription($target.getData('subscription-id'));
        break;
    }
  },

  removeSubscription: function(id) {
    if (this.removing) {
      return;
    }
    this.removing = true;

    LKAPIClient.removeSalesReportSubscription(id, {
      onSuccess: function() {
        this.reload();
      },
      onComplete: function() {
        delete this.removing;
      },
      context: this
    });
  },

  onSubmitEmail: function(evt) {
    evt.preventDefault();

    if (this.subscribing) {
      return;
    }
    this.subscribing = true;

    var callbacks = {
      onSuccess: function() {
        this.reload();
      },
      onComplete: function() {
        delete this.subscribing;
      },
      context: this
    };

    var email = null;
    var emailInput = evt.target.get('input[type=email]');
    if (emailInput) {
      email = emailInput.value();
    }

    if (!email || email == this.user['email']) {
      LKAPIClient.subscribeToSalesReportsWithMyEmail(callbacks);
    } else {
      LKAPIClient.subscribeToSalesReportsWithEmail(email, callbacks);
    }
  }

});
