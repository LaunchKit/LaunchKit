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
var cookies = skit.platform.cookies;
var iter = skit.platform.iter;
var navigation = skit.platform.navigation;
var urls = skit.platform.urls;
var Handlebars = skit.thirdparty.handlebars;

var ButtonOverlay = library.overlays.ButtonOverlay;
var AmbiguousProgressOverlay = library.overlays.AmbiguousProgressOverlay;
var Dashboard = library.controllers.Dashboard;
var LKAPIClient = library.api.LKAPIClient;
var itunessearch = library.misc.itunessearch;
var introHtml = library.products.dashboardintro;

var html = __module__.html;
var nuxHtml = __module__.nux.html;
var reviewHtml = __module__.review.html;
var supportEmailHtml = __module__.support_email.html;


var SEEN_HIGHLIGHTED_REVIEW_COOKIE = 'seen-reviews';

function sameHostReferer() {
  var referer = navigation.referer();
  if (!referer) {
    return false;
  }

  var parsed = urls.parse(referer);
  return parsed.host == navigation.host();
}


function emailUrlForReview(r) {
  var subject = 'Please look into this ' + r.rating + ' star review for ' + r.app.names.short + ' v' + r.appVersion
  var body = supportEmailHtml(r);
  var emailUrl = urls.appendParams('mailto:', {
    subject: subject,
    body: body
  });

  return emailUrl;
}


Handlebars.registerHelper('supportEmailUrl', function(review) {
  return emailUrlForReview(review);
});
Handlebars.registerHelper('itunesCountryName', function(countryCode) {
  return itunessearch.COUNTRIES_BY_CODE[countryCode] || 'N/A';
});


module.exports = Controller.create(Dashboard, {
  __preload__: function(done) {
    var query = navigation.query();
    if (sameHostReferer() && query['itunes_id']) {
      // Handle new app flow from onboarding.
      LKAPIClient.addReviewsAppWithId(query['country'] || 'us', query['itunes_id'], query['include_related'] == '1', {
        onComplete: function() {
          var strippedUrl = urls.parse(navigation.url()).path;
          navigation.navigate(strippedUrl);
          done();
        }
      });
      return;
    }

    // LOAD NORMALLY

    var i = 4;
    function maybeFinish() {
      i--;
      if (i != 0) {
        return;
      }

      if (this.apps && this.apps.length && this.user['needsReviewsOnboarding']) {
        navigation.navigate('/reviews/dashboard/setup-slack/');
      }

      done();
    }

    var params = this.reviewsParams();
    // Smaller initial pageload.
    params['limit'] = 10;

    LKAPIClient.reviews(params, {
      onSuccess: function(reviews) {
        this.reviews = reviews;
      },
      onComplete: maybeFinish,
      context: this
    });
    LKAPIClient.reviewSubscriptions({
      onSuccess: function(subscriptions) {
        this.subscriptions = subscriptions;
      },
      onComplete: maybeFinish,
      context: this
    });
    LKAPIClient.twitterAppConnections({
      onSuccess: function(connections, unconnectedApps, twitterHandles) {
        this.twitterConnections = connections;
      },
      onComplete: maybeFinish,
      context: this
    });
    LKAPIClient.reviewsApps({
      onSuccess: function(apps) {
        var iTunesIdsSeen = {};
        iter.forEach(apps, function(app, i) {
          var iTunesId = app['iTunesId'];
          iTunesIdsSeen[iTunesId] = (iTunesIdsSeen[iTunesId] || 0) + 1;
        });

        iter.forEach(apps, function(app) {
          var iTunesId = app['iTunesId'];
          if (iTunesIdsSeen[iTunesId] > 1) {
            app.showCountry = true;
          }
        });

        this.apps = apps;
      },
      onComplete: maybeFinish,
      context: this
    });
  },

  __title__: function() {
    return 'Review Monitor';
  },

  __body__: function() {

    // INGESTING CONTENT PLEASE WAIT VIEW

    var userHasPending = this.user['reviewsPending'];
    var showNux = userHasPending || navigation.query()['nux'] == '1';

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

    if (showNux) {
      return {
        content: nuxHtml()
      };
    }

    // NO APPS YET VIEW

    if (!this.apps.length) {
      return {
        content: introHtml({product: this.product})
      };
    }

    // NORMAL VIEW

    var selectedStars = null;
    if (this.starsFilter) {
      selectedStars = '★★★★★'.substring(0, this.starsFilter);
    }

    var highlightedReview = null;
    if (!cookies.get(SEEN_HIGHLIGHTED_REVIEW_COOKIE) && this.reviews) {
      iter.forEach(this.reviews, function(review, i, stop) {
        if (review.rating == 5 && review.imageUrl) {
          highlightedReview = review;
          stop();
        }
      });
    }

    return {
      content: html({
        reviews: this.reviews,
        loading: this.reviews == null,
        hasApps: this.apps.length,
        highlightedReview: highlightedReview,
        selectedStars: selectedStars,
        apps: this.apps,
        selectedApp: this.selectedApp,
        slackSubscription: slackSubscription,
        emailSubscriptions: emailSubscriptions,
        myEmailSubscription: myEmailSubscription,
        hasEmailSubscription: myEmailSubscription || emailSubscriptions.length > 0,
        twitterConnections: this.twitterConnections,
        user: this.user
      })
    };
  },

  __ready__: function() {
    var slackForm = dom.get('#slack-add-form');
    if (slackForm) {
      this.bind(slackForm, 'submit', this.onSubmitSlack, this);
    }

    var emailForm = dom.get('#email-add-form');
    if (emailForm) {
      this.bind(emailForm, 'submit', this.onSubmitEmail, this);
    }

    this.bind(window, 'scroll', this.onScrollWindow, this);

    var hide = dom.get('.hide-highlighted-review');
    if (hide) {
      this.bind(hide, 'click', this.onClickHideReview, this);
    }
  },

  onClickHideReview: function(evt) {
    var host = navigation.host().split(':')[0];
    // Domains need at least two periods. What?
    // http://stackoverflow.com/questions/1134290/
    if (host == 'localhost') {
      host = '';
    } else if (host == 'launchkit.io') {
      host = '.' + host;
    }

    var expiry = new Date((+new Date()) + (365 * 24 * 60 * 60 * 1000));
    cookies.set(SEEN_HIGHLIGHTED_REVIEW_COOKIE, '1', {domain: host, expires: expiry});
  },

  onScrollWindow: function(evt) {
    if (this.isOnLastPage()) {
      this.maybeLoadMore();
    }
  },

  maybeLoadMore: function() {
    if (this.loadingMore || !this.reviews || !this.reviews.length || this.noMoreReviews) {
      return;
    }
    this.loadingMore = true;

    LKAPIClient.reviews(this.reviewsParams(true), {
      onSuccess: function(reviews) {
        if (!reviews.length) {
          this.noMoreReviews = true;
          return;
        }

        this.reviews = this.reviews.concat(reviews);
        var renderedReviews = iter.map(reviews, function(r) {
          return reviewHtml(r);
        }).join('');
        dom.get('li.review').parent().append(renderedReviews);
      },
      onComplete: function() {
        delete this.loadingMore;
      },
      context: this
    })
  },

  reviewsParams: function(opt_loadMore) {
    var lastReview;
    if (opt_loadMore && this.reviews && this.reviews.length) {
      lastReview = this.reviews[this.reviews.length - 1];
    }

    return {
      startReviewId: lastReview && lastReview['id'],
      rating: this.starsFilter,
      appId: this.selectedApp ? this.selectedApp['id'] : null,
      country: this.selectedApp ? this.selectedApp['country'] : null
    };
  },

  refreshFeed: function() {
    this.reviews = null;
    delete this.noMoreReviews;

    this.rerender();
    LKAPIClient.reviews(this.reviewsParams(), {
      onSuccess: function(reviews) {
        this.reviews = reviews;
        this.rerender();
      },
      context: this
    });
  },

  handleAction: function(action, $target) {
    Dashboard.prototype.handleAction.apply(this, arguments);

    switch(action) {
      case 'apps-add':
        navigation.navigate('/reviews/onboard/');
        break;

      case 'filter':
        var filter = $target.getData('filter');
        var value = $target.getData('value');
        if (filter == 'stars'){
          this.starsFilter = value ? +value : null;
        } else if (filter == 'app') {
          this.selectedApp = iter.find(this.apps, function(app) {
            return app['id'] == $target.getData('id') && app['country'] == $target.getData('country');
          });
        }
        this.refreshFeed();
        break;

      case 'slack-review-filter-good':
        var el = $target.element;
        var checked = el.checked;
        setTimeout(function() {
          // evt.preventDefault() on this causes it to not fire, so
          // set this again after the event handler is done.
          el.checked = checked;
        }, 0);
        this.markSubscriptionFiltered($target.getData('subscription-id'), checked);
        break;

      case 'remove-subscription':
        this.removeSubscription($target.getData('subscription-id'));
        break;

      case 'remove-app':
        var app = iter.find(this.apps, function(app) {
          return app['id'] == $target.getData('id') && app['country'] == $target.getData('country');
        });

        if (app) {
          this.maybeRemoveApp(app, $target);
        }
        break;

      default:
        break;
    }

  },

  maybeRemoveApp: function(app) {
    var confirm = new ButtonOverlay('Remove ' + app.names.short + '?', 'You can add it back later if you change your mind.');
    confirm.addButton('Remove', function() {
      this.removeApp(app);
    }, this);
    confirm.addButton('Cancel');
    confirm.show();
  },

  removeApp: function(app) {
    var progress = new AmbiguousProgressOverlay('Removing...');
    progress.show();

    var removedAppId = app.id;
    var removedAppCountry = app.country;
    LKAPIClient.removeReviewsAppWithId(removedAppCountry, removedAppId, {
      onSuccess: function() {
        this.selectedApp = null;
        this.apps = iter.filter(this.apps, function(app) {
          if (app.id == removedAppId && app.country == removedAppCountry) {
            return false;
          }
          return true;
        })
        this.reload();
      },
      onComplete: function() {
        progress.done();
      },
      context: this
    });
  },

  onSubmitSlack: function(evt) {
    evt.preventDefault();

    var textInput = evt.target.get('input[type=text]');
    var url = textInput.value() || '';
    var parsed = urls.parse(url);
    if (!parsed || parsed.host != 'hooks.slack.com' || parsed.path.indexOf('/services') != 0) {
      textInput.element.focus();
      textInput.element.select();
      return;
    }

    if (this.subscribing) {
      return;
    }
    this.subscribing = true;

    LKAPIClient.subscribeToReviews(null, url, {
      onSuccess: function() {
        this.reload();
      },
      onComplete: function() {
        delete this.subscribing;
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
      LKAPIClient.subscribeToReviewsWithMyEmail(callbacks);
    } else {
      LKAPIClient.subscribeToReviewsWithEmail(email, callbacks);
    }
  },

  removeSubscription: function(id) {
    if (this.removing) {
      return;
    }
    this.removing = true;

    LKAPIClient.removeReviewSubscription(id, {
      onSuccess: function() {
        this.reload();
      },
      onComplete: function() {
        delete this.removing;
      },
      context: this
    });
  },

  markSubscriptionFiltered: function(id, filterGood) {
    if (this.updatingFilter) {
      return;
    }
    this.updatingFilter = true;

    LKAPIClient.markSubscriptionFilterGood(id, filterGood, {
      onComplete: function() {
        delete this.updatingFilter;
      },
      context: this
    });
  }
});
