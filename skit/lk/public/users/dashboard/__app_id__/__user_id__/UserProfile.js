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
var iter = skit.platform.iter;
var navigation = skit.platform.navigation;
var urls = skit.platform.urls;
var util = skit.platform.util;
var Handlebars = skit.thirdparty.handlebars;

var LKAnalyticsAPIClient = library.api.LKAnalyticsAPIClient;
var Dashboard = library.controllers.Dashboard;
var moment = third_party.moment;
// Require this here to get helpers.
var _ = public.users.dashboard.__app_id__.SuperUsersAppDash;

var html = __module__.html;


function floatingDaysActive(daysActive) {
  var visitsByTimestamp = {};
  iter.forEach(daysActive, function(summary) {
    var d = '' + Math.round(summary[0] * 1000);
    visitsByTimestamp[d] = summary[1];
  });

  var ONE_DAY = 24 * 60 * 60 * 1000;

  var days = [];
  var moreThanAMonthAgo = (+(new Date())) - (ONE_DAY * 167);
  moreThanAMonthAgo -= moreThanAMonthAgo % ONE_DAY;
  // start on Sunday
  while ((new Date(moreThanAMonthAgo)).getDay() != 0) {
    moreThanAMonthAgo += ONE_DAY;
  }

  // now we have a Sunday that is more than a month ago.
  var now = +(new Date());
  var current = moreThanAMonthAgo;
  while (current < now) {
    var className = '';

    var visits = visitsByTimestamp[current] || 0;
    var title = 'no visits';
    if (visits) {
      if (visits > 6) {
        className = 'heavy';
      } else if (visits > 3) {
        className = 'medium';
      } else if (visits) {
        className = 'light';
      }

      title = visits + ' visit' + (visits == 1 ? '' : 's');
    }

    var d = new Date(current);
    days.push({
      title: '' + moment(d).format('L') + ': ' + title,
      className: className,
      date: d
    });
    current += ONE_DAY;
  }

  var columns = (days.length / 7);
  var today = now - (now % ONE_DAY);

  var floatingDays = [];
  var lastMonth = moment(days[0].date).format('MMMM');
  for (var i = 0; i < columns; i++) {
    var day = days[Math.min(i * 7 + 7, days.length - 1)];
    var date = new Date();
    var month = moment(day.date).format('MMMM');
    if (lastMonth != month) {
      floatingDays.push({className: 'label', body: month.substring(0, 3)});
      lastMonth = month;
    } else {
      floatingDays.push({className: 'empty'});
    }
  }

  for (var i = 0; i < 7; i++) {
    for (var j = 0; j < columns; j++) {
      var day = days[i + (j * 7)];
      if (day) {
        if (j == 0) {
          var body = ('' + new Date(day.date)).substring(0,1);
          floatingDays.push({className: 'label first', body: body})
        }
        if (+day.date == today) {
          day.className += ' today';
        }
        floatingDays.push(day);
      }
    }
  }

  return floatingDays;
}


module.exports = Controller.create(Dashboard, {
  __preload__: function(done) {
    var i = 2;
    function maybeFinish() {
      if (!--i) {
        done();
      }
    }

    var userId = this.params['__user_id__'];
    LKAnalyticsAPIClient.userDetails(userId, {
      onSuccess: function(sdkUser, sdkClientUser, app, daysActive) {
        this.sdkUser = sdkUser;
        this.sdkClientUser = sdkClientUser;
        this.app = app;
        this.daysActive = daysActive;
      },
      onError: function(code) {
        if (code == 404) {
          navigation.notFound();
        } else {
          // error page
          throw new Error('Code: ' + code);
        }
      },
      onComplete: maybeFinish,
      context: this
    });

    LKAnalyticsAPIClient.visits({'sdk_user_id': userId}, {
      onSuccess: function(visits) {
        this.visits = visits;
      },
      onComplete: maybeFinish,
      context: this
    });
  },

  __title__: function() {
    return this.sdkUser.name || 'Anonymous User';
  },

  __body__: function() {
    return html({
      sdkUser: this.sdkUser,
      sdkClientUser: this.sdkClientUser,
      app: this.app,
      visits: this.visits,
      floatingDaysActive: floatingDaysActive(this.daysActive)
    });
  },

  handleAction: function(name, $target) {
    Dashboard.prototype.handleAction.apply(this, arguments);

    switch (name) {
      default:
        break;
    }
  }
});
