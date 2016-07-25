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

var iter = skit.platform.iter;
var util = skit.platform.util;

var LKAPIClientBase = library.api.LKAPIClientBase;


function LKAPIClient() {}
util.inherits(LKAPIClient, LKAPIClientBase);


LKAPIClient.prototype.healthCheck = function(callbacks) {
  this.send_('debug/health_check', {
    method: 'GET',
    callbacks: callbacks
  });
};


LKAPIClient.prototype.screenshotWithUploadId = function(uploadId, callbacks) {
  this.send_('screenshot_images', {
    method: 'POST',
    params: {'upload_id': uploadId},
    parse: function(data) {
      return [data['image']];
    },
    callbacks: callbacks
  });
};


LKAPIClient.prototype.backgroundWithUploadId = function(uploadId, callbacks) {
  this.send_('background_images', {
    method: 'POST',
    params: {'upload_id': uploadId},
    parse: function(data) {
      return [data['image']];
    },
    callbacks: callbacks
  });
};


LKAPIClient.prototype.websiteIconWithUploadId = function(uploadId, callbacks) {
  this.send_('website_icon_images', {
    method: 'POST',
    params: {'upload_id': uploadId},
    parse: function(data) {
      return [data['image']];
    },
    callbacks: callbacks
  });
};


LKAPIClient.prototype.websiteLogoWithUploadId = function(uploadId, callbacks) {
  this.send_('website_logo_images', {
    method: 'POST',
    params: {'upload_id': uploadId},
    parse: function(data) {
      return [data['image']];
    },
    callbacks: callbacks
  });
};


LKAPIClient.prototype.websiteBackgroundWithUploadId = function(uploadId, callbacks) {
  this.send_('website_background_images', {
    method: 'POST',
    params: {'upload_id': uploadId},
    parse: function(data) {
      return [data['image']];
    },
    callbacks: callbacks
  });
};


LKAPIClient.prototype.websiteScreenshotWithUploadId = function(uploadId, callbacks) {
  this.send_('website_screenshot_images', {
    method: 'POST',
    params: {'upload_id': uploadId},
    parse: function(data) {
      return [data['image']];
    },
    callbacks: callbacks
  });
};


LKAPIClient.prototype.signup = function(firstName, lastName, email, password, callbacks) {
  this.send_('signup', {
    method: 'POST',
    params: {
      'first_name': firstName,
      'last_name': lastName,
      'email': email,
      'password': password
    },
    callbacks: callbacks
  });
};


LKAPIClient.prototype.login = function(email, password, callbacks) {
  var params = {
    grant_type: 'password',
    scope: 'readwrite',
    username: email,
    password: password
  };
  this.send_('oauth2/token', {
    method: 'POST',
    params: params,
    callbacks: callbacks
  });
};


LKAPIClient.prototype.logout = function(callbacks) {
  this.send_('logout', {
    method: 'POST',
    callbacks: callbacks
  });
};


LKAPIClient.prototype.resetPassword = function(email, callbacks) {
  this.send_('reset_password', {
    params: {'email': email},
    method: 'POST',
    callbacks: callbacks
  });
};

LKAPIClient.prototype.setNewPassword = function(token, password, callbacks) {
  this.send_('reset_password/finish', {
    params: {'token': token, 'password': password},
    method: 'POST',
    callbacks: callbacks
  });
};

LKAPIClient.prototype.verifyEmailWithToken = function(token, callbacks) {
  this.send_('verify_email', {
    params: {'token': token},
    method: 'POST',
    callbacks: callbacks
  });
};

LKAPIClient.prototype.unsubscribeWithToken = function(token, callbacks) {
  this.send_('unsubscribe', {
    params: {'token': token},
    method: 'POST',
    callbacks: callbacks
  });
};

LKAPIClient.prototype.user = function(callbacks) {
  var allCallbacks = [{
    onSuccess: function(user) {
      this.currentUser = user;
    },
    context: this
  }];
  allCallbacks.push(callbacks);

  this.send_('user', {
    parse: function(data) {
      return [data['user']];
    },
    callbacks: allCallbacks
  });
};


var parseDetailsResponse = function(data) {
  return [data['user'], data['settings'], data['emails']];
};

LKAPIClient.prototype.userDetails = function(callbacks) {
  var allCallbacks = [{
    onSuccess: function(user) {
      this.currentUser = user;
    },
    context: this
  }];
  allCallbacks.push(callbacks);

  this.send_('user/details', {
    parse: parseDetailsResponse,
    callbacks: allCallbacks
  });
};


LKAPIClient.prototype.updateUserDetails = function(fields, callbacks) {
  this.send_('user/details', {
    method: 'POST',
    params: fields,
    parse: parseDetailsResponse,
    callbacks: callbacks
  });
};

LKAPIClient.prototype.setHasBeenReviewsOnboarded = function(callbacks) {
  var fields = {'has_reviews_onboarded': '1'};
  this.updateUserDetails(fields, callbacks);
};

LKAPIClient.prototype.setHasBeenSalesOnboarded = function(callbacks) {
  var fields = {'has_sales_onboarded': '1'};
  this.updateUserDetails(fields, callbacks);
};

LKAPIClient.prototype.updateUserPhoto = function(gaeUploadId, callbacks) {
  var fields = {'gae_upload_id': gaeUploadId};
  this.updateUserDetails(fields, callbacks);
};

LKAPIClient.prototype.deleteUserAccount = function(myEmailConfirmation, callbacks) {
  this.send_('user/delete', {
    method: 'POST',
    params: {'email': myEmailConfirmation},
    callbacks: callbacks
  });
};


LKAPIClient.prototype.addEmailAddress = function(email, callbacks) {
  this.send_('user/emails', {
    method: 'POST',
    params: {'email': email},
    parse: function(data) {
      return [data['email']]
    },
    callbacks: callbacks
  });
};
LKAPIClient.prototype.removeEmailAddress = function(email, callbacks) {
  this.send_('user/emails/delete', {
    method: 'POST',
    params: {'email': email},
    parse: function(data) {
      return [data['emails']]
    },
    callbacks: callbacks
  });
};
LKAPIClient.prototype.requestVerificationEmail = function(email, callbacks) {
  this.send_('user/emails/request_verification', {
    method: 'POST',
    params: {'email': email},
    parse: function(data) {
      return [data['emails']]
    },
    callbacks: callbacks
  });
};
LKAPIClient.prototype.setEmailAddressPrimary = function(email, callbacks) {
  this.send_('user/emails/set_primary', {
    method: 'POST',
    params: {'email': email},
    parse: function(data) {
      return [data['emails']]
    },
    callbacks: callbacks
  });
};


LKAPIClient.prototype.slackTokenFromCode = function(code, service, onboarding, callbacks) {
  this.send_('slack', {
    method: 'POST',
    params: {'code': code, 'service': service, 'onboarding': onboarding ? '1': '0'},
    callbacks: callbacks
  });
};


LKAPIClient.prototype.slackChannels = function(callbacks) {
  this.send_('slack/channels', {
    method: 'GET',
    parse: function(data) {
      return [data['tokenValid'], data['channels']];
    },
    callbacks: callbacks
  });
};


LKAPIClient.prototype.slackUsage = function(callbacks) {
  this.send_('slack/usage', {
    method: 'GET',
    parse: function(data) {
      return [data['connected'], data['channelsByProduct']];
    },
    callbacks: callbacks
  });
};


LKAPIClient.prototype.slackDisconnect = function(callbacks) {
  this.send_('slack/disconnect', {
    method: 'POST',
    callbacks: callbacks
  });
};


LKAPIClient.prototype.twitterConnect = function(appId, callbackUrl, callbacks) {
  this.send_('twitter/connect', {
    method: 'GET',
    params: {'app_id': appId, 'callback_url': callbackUrl},
    parse: function(data) {
      return [data['twitterConnectUrl']];
    },
    callbacks: callbacks
  });
};


LKAPIClient.prototype.twitterConnectFinish = function(token, verifier, appId, callbacks) {
  this.send_('twitter/finish', {
    method: 'POST',
    params: {'token': token, 'verifier': verifier, 'app_id': appId},
    callbacks: callbacks
  });
};


//
// APP STORE
//


LKAPIClient.prototype.appStoreInfo = function(country, appId, callbacks) {
  this.send_('appstore/' + country + '/' + appId, {
    method: 'GET',
    parse: function(data) {
      return [data['app'], data['related']];
    },
    callbacks: callbacks
  });
};


LKAPIClient.prototype.reviewsApps = function(callbacks) {
  this.send_('apps', {
    method: 'GET',
    parse: function(data) {
      return [data['apps']];
    },
    callbacks: callbacks
  });
};


LKAPIClient.prototype.addReviewsAppWithId = function(country, iTunesId, includeRelated, callbacks) {
  this.send_('apps', {
    method: 'POST',
    params: {
      'itunes_id': iTunesId,
      'country': country,
      'include_related': includeRelated ? '1': '0'
    },
    parse: function(data) {
      return [data['apps']];
    },
    callbacks: callbacks
  });
};

LKAPIClient.prototype.removeReviewsAppWithId = function(country, appId, callbacks) {
  this.send_('apps/' + country + '/' + appId + '/delete', {
    method: 'POST',
    callbacks: callbacks
  });
};


//
// REVIEWS
//


LKAPIClient.prototype.reviewSubscriptions = function(callbacks) {
  this.send_('reviews/subscriptions', {
    method: 'GET',
    parse: function(data) {
      return [data['subscriptions']];
    },
    callbacks: callbacks
  });
};


LKAPIClient.prototype.subscribeToReviewsWithEmail = function(email, callbacks) {
  this.send_('reviews/subscriptions', {
    method: 'POST',
    params: {'email': email},
    parse: function(data) {
      return [data['subscription']];
    },
    callbacks: callbacks
  });
};


LKAPIClient.prototype.subscribeToReviewsWithMyEmail = function(callbacks) {
  this.send_('reviews/subscriptions', {
    method: 'POST',
    params: {'my_email': '1'},
    parse: function(data) {
      return [data['subscription']];
    },
    callbacks: callbacks
  });
};


LKAPIClient.prototype.subscribeToReviewsWithSlackChannel = function(channelName, callbacks) {
  this.send_('reviews/subscriptions', {
    method: 'POST',
    params: {'slack_channel_name': channelName || ''},
    parse: function(data) {
      return [data['subscription']];
    },
    callbacks: callbacks
  });
};


LKAPIClient.prototype.subscribeToReviewsWithSlackUrl = function(url, callbacks) {
  this.send_('reviews/subscriptions', {
    method: 'POST',
    params: {'slack_url': url},
    parse: function(data) {
      return [data['subscription']];
    },
    callbacks: callbacks
  });
};


LKAPIClient.prototype.subscribeToReviewsWithTwitter = function(twitterAppConnectionId, callbacks) {
  this.send_('reviews/subscriptions', {
    method: 'POST',
    params: {'twitter_app_connection_id': twitterAppConnectionId},
    parse: function(data) {
      return [data['subscription']];
    },
    callbacks: callbacks
  });
};


LKAPIClient.prototype.autoSubscribeToReviewsWithTwitter = function(appId, callbacks) {
  this.send_('reviews/subscriptions', {
    method: 'POST',
    params: {'app_id': appId},
    parse: function(data) {
      return [data['subscription']];
    },
    callbacks: callbacks
  });
};


LKAPIClient.prototype.connectAppToTwitter = function(appId, twitterHandle, callbacks) {
  this.send_('twitter/connect_app', {
    method: 'POST',
    params: {'app_id': appId, 'twitter_handle': twitterHandle},
    callbacks: callbacks
  });
};


LKAPIClient.prototype.disconnectAppFromTwitter = function(connectionId, callbacks) {
  this.send_('twitter/disconnect_app', {
    method: 'POST',
    params: {'connection_id': connectionId},
    callbacks: callbacks
  });
};


LKAPIClient.prototype.twitterAppConnections = function(callbacks) {
  this.send_('twitter/connections', {
    method: 'GET',
    parse: function(data) {
      return [data['connections'], data['unconnectedApps'], data['handles']];
    },
    callbacks: callbacks
  });
};


LKAPIClient.prototype.removeReviewSubscription = function(subId, callbacks) {
  this.send_('reviews/subscriptions/' + subId + '/delete', {
    method: 'POST',
    callbacks: callbacks
  });
};


LKAPIClient.prototype.removeSubscriptionWithToken = function(token, callbacks) {
  this.send_('reviews/subscriptions/unsubscribe', {
    params: {'token': token},
    method: 'POST',
    callbacks: callbacks
  });
};


LKAPIClient.prototype.markSubscriptionFilterGood = function(subId, doFilterGood, callbacks) {
  this.send_('reviews/subscriptions/' + subId, {
    method: 'POST',
    params: {'filter_good': doFilterGood ? '1' : '0'},
    callbacks: callbacks
  });
};


function decorateReview(r, appsById) {
  r.app = appsById[r.appId];
  r.stars = '★★★★★'.substring(0, r.rating);
  r.emptyStars = '★★★★★'.substring(0, Math.min(-1 * (r.rating - 5), 5));

  r.needsTriage = r.rating < 4;
}


LKAPIClient.prototype.reviews = function(options, callbacks) {
  var params = {
    rating: options.rating || '',
    app_id: options.appId || '',
    start_review_id: options.startReviewId || '',
    limit: options.limit || '',
    country: options.country || ''
  };

  this.send_('reviews', {
    method: 'GET',
    params: params,
    parse: function(data) {
      var reviews = data['reviews'];
      var appsById = data['apps'];
      iter.forEach(reviews, function(r) {
        decorateReview(r, appsById);
      });
      return [reviews];
    },
    callbacks: callbacks
  });
};


LKAPIClient.prototype.review = function(reviewId, callbacks) {
  this.send_('reviews/' + reviewId, {
    method: 'GET',
    parse: function(data) {
      var review = data['review'];
      var appsById = data['apps'];
      decorateReview(review, appsById);
      return [review];
    },
    callbacks: callbacks
  })
};


LKAPIClient.prototype.tweetReview = function(twitterHandle, reviewId, tweetText, callbacks) {
  this.send_('twitter/tweet_review', {
    method: 'POST',
    params: {'twitter_handle': twitterHandle, 'review_id': reviewId, 'tweet_text': tweetText},
    callbacks: callbacks
  })
};


//
// SALES AND ITUNES CONNECT
//


LKAPIClient.prototype.salesMetrics = function(requestedDate, callbacks) {
  var date = null;
  if (requestedDate) {
    date = (+requestedDate) / 1000.0;
  }
  this.send_('itunes/sales_metrics', {
    method: 'GET',
    params: {'requested_date': date},
    callbacks: callbacks
  });
};


LKAPIClient.prototype.itunesConnect = function(appleId, password, callbacks) {
  this.send_('itunes/connect', {
    method: 'POST',
    params: {'apple_id': appleId, 'password': password},
    callbacks: callbacks
  });
};


LKAPIClient.prototype.disconnectItunes = function(callbacks) {
  this.send_('itunes/disconnect', {
    method: 'POST',
    callbacks: callbacks
  });
};


LKAPIClient.prototype.itunesVendors = function(callbacks) {
  this.send_('itunes/vendors', {
    method: 'GET',
    parse: function(data) {
      return [data['appleId'], data['vendors']]
    },
    callbacks: callbacks
  });
};


LKAPIClient.prototype.chooseVendor = function(vendorId, callbacks) {
  this.send_('itunes/choose_vendor', {
    method: 'POST',
    params: {'vendor_id': vendorId},
    callbacks: callbacks
  });
};


LKAPIClient.prototype.salesReportSubscriptions = function(callbacks) {
  this.send_('itunes/subscriptions', {
    method: 'GET',
    parse: function(data) {
      return [data['subscriptions']];
    },
    callbacks: callbacks
  });
};


LKAPIClient.prototype.subscribeToSalesReportsWithEmail = function(email, callbacks) {
  this.send_('itunes/subscriptions', {
    method: 'POST',
    params: {'email': email},
    parse: function(data) {
      return [data['subscription']];
    },
    callbacks: callbacks
  });
};


LKAPIClient.prototype.subscribeToSalesReportsWithMyEmail = function(callbacks) {
  this.send_('itunes/subscriptions', {
    method: 'POST',
    params: {'my_email': '1'},
    parse: function(data) {
      return [data['subscription']];
    },
    callbacks: callbacks
  });
};


LKAPIClient.prototype.subscribeToSalesReportsWithSlackUrl = function(url, callbacks) {
  this.send_('itunes/subscriptions', {
    method: 'POST',
    params: {'slack_url': url},
    parse: function(data) {
      return [data['subscription']];
    },
    callbacks: callbacks
  });
};


LKAPIClient.prototype.subscribeToSalesReportsWithSlackChannel = function(channelName, callbacks) {
  this.send_('itunes/subscriptions', {
    method: 'POST',
    params: {'slack_channel_name': channelName || ''},
    parse: function(data) {
      return [data['subscription']];
    },
    callbacks: callbacks
  });
};


LKAPIClient.prototype.removeSalesReportSubscription = function(subId, callbacks) {
  this.send_('itunes/subscriptions/' + subId + '/delete', {
    method: 'POST',
    callbacks: callbacks
  });
};


LKAPIClient.prototype.removeSalesReportSubscriptionWithToken = function(token, callbacks) {
  this.send_('itunes/subscriptions/unsubscribe', {
    params: {'token': token},
    method: 'POST',
    callbacks: callbacks
  });
};


//
// SCREENSHOT BUILDER
//


LKAPIClient.prototype.addScreenshotSet = function(appName, appVersion, platform, callbacks) {
  this.send_('screenshot_sets', {
    method: 'POST',
    params: {'name': appName, 'version': appVersion, 'platform': platform},
    parse: function(data) {
      var set = data['set'];
      return [set];
    },
    callbacks: callbacks
  });
};


LKAPIClient.prototype.screenshotSets = function(callbacks) {
  this.send_('screenshot_sets', {
    method: 'GET',
    parse: function(data) {
      var sets = data['sets'];
      return [sets];
    },
    callbacks: callbacks
  });
};


LKAPIClient.prototype.screenshotSetAndShots = function(setId, callbacks) {
  this.send_('screenshot_sets/' + setId, {
    method: 'GET',
    parse: function(data) {
      var set = data['set'];
      var shots = data['shots'];
      return [set, shots];
    },
    callbacks: callbacks
  });
};

LKAPIClient.prototype.deleteScreenshotSet = function(setId, callbacks) {
  this.send_('screenshot_sets/' + setId + '/delete', {
    method: 'POST',
    callbacks: callbacks
  })
};

LKAPIClient.prototype.updateScreenshotSet = function(setId, fields, callbacks) {
  this.send_('screenshot_sets/' + setId, {
    method: 'POST',
    params: fields,
    parse: function(data) {
      return [data['set']];
    },
    callbacks: callbacks
  })
};


LKAPIClient.prototype.duplicateScreenshotSet = function(setId, name, version, platform, callbacks) {
  this.send_('screenshot_sets/' + setId + '/duplicate', {
    method: 'POST',
    params: {'name': name, 'version': version, 'platform': platform},
    parse: function(data) {
      return [data['set']];
    },
    callbacks: callbacks
  });
};


LKAPIClient.prototype.addScreenshotSetBundle = function(setId, hq, uploadIds, uploadNames, callbacks) {
  var qs = 'hq=' + (hq ? '1' : '0');
  for (var i = 0; i < uploadIds.length; i++) {
    qs += '&upload_id=' + encodeURIComponent(uploadIds[i]) + '&upload_name=' + encodeURIComponent(uploadNames[i]);
  }
  this.send_('screenshot_sets/' + setId + '/create_bundle', {
    method: 'POST',
    params: qs,
    parse: function(data) {
      return [data['bundleId']]
    },
    callbacks: callbacks
  });
};

LKAPIClient.prototype.screenshotSetBundleStatus = function(bundleId, callbacks) {
  this.send_('screenshot_sets/bundle_status/' + bundleId, {
    method: 'GET',
    parse: function(data) {
      return [data['status']];
    },
    callbacks: callbacks
  });
};

LKAPIClient.prototype.screenshotSetDownloadUrl = function(setId, bundleId, token, callbacks) {
  this.send_('screenshot_sets/' + setId + '/download', {
    method: 'GET',
    params: {'bundle_id': bundleId, 'token': token},
    parse: function(data) {
      return [data['downloadUrl']];
    },
    callbacks: callbacks
  });
};


LKAPIClient.prototype.addShot = function(setId, formFields, callbacks) {
  this.send_('screenshot_sets/' + setId + '/add_shot', {
    method: 'POST',
    params: formFields,
    parse: function(data) {
      var shot = data['shot'];
      return [shot];
    },
    callbacks: callbacks
  })
};


LKAPIClient.prototype.updateShot = function(setId, shotId, formFields, callbacks) {
  this.send_('screenshot_sets/' + setId + '/' + shotId, {
    method: 'POST',
    params: formFields,
    parse: function(data) {
      var shot = data['shot'];
      return [shot];
    },
    callbacks: callbacks
  });
};


LKAPIClient.prototype.deleteShot = function(setId, shotId, callbacks) {
  this.send_('screenshot_sets/' + setId + '/' + shotId + '/delete', {
    method: 'POST',
    parse: function(data) {
      var shot = data['shot'];
      return [shot];
    },
    callbacks: callbacks
  });
};

LKAPIClient.prototype.addShotOverride = function(setId, shotId, imageId, deviceType, callbacks) {
  this.send_('screenshot_sets/' + setId + '/' + shotId + '/' + deviceType, {
    method: 'POST',
    params: {'image_id':imageId},
    parse: function(data) {
      var override = data['override'];
      return [override]
    },
    callbacks: callbacks
  })
};

LKAPIClient.prototype.deleteShotOverride = function(setId, shotId, deviceType, callbacks) {
  this.send_('screenshot_sets/' + setId + '/' + shotId + '/' + deviceType + '/delete', {
    method: 'POST',
    parse: function(data) {
      var shot = data['shot'];
      return [shot]
    },
    callbacks: callbacks
  })
};


// APP WEBSITES


LKAPIClient.prototype.getAllWebsites = function(callbacks) {
  this.send_('websites', {
    method: 'GET',
    parse: function(data) {
      return [data['websites']];
    },
    callbacks: callbacks
  });
};


LKAPIClient.prototype.trackWebsiteView = function(websiteId, host, referer, userAgent, path, callbacks) {
  var params = {
    'website_id': websiteId,
    'host': host,
    'referer': referer,
    'user_agent': userAgent,
    'path': path || ''
  };

  this.send_('websites/track', {
    method: 'POST',
    params: params,
    callbacks: callbacks
  });
};


LKAPIClient.prototype.getWebsite = function(id, callbacks) {
  this.send_('websites/' + id, {
    method: 'GET',
    parse: function(data) {
      return [data['website']];
    },
    callbacks: callbacks
  });
};

LKAPIClient.prototype.getFullWebsite = function(id, callbacks) {
  this.send_('websites/' + id + '?get_website_and_pages=1', {
    method: 'GET',
    parse: function(data) {
      return [data['website']];
    },
    callbacks: callbacks
  });
};

LKAPIClient.prototype.getWebsitePage = function(id, slug, callbacks) {
  this.send_('websites/' + id + '/' + slug, {
    method: 'GET',
    parse: function(data) {
      return [data['website'], data['page']];
    },
    callbacks: callbacks
  });
};


LKAPIClient.prototype.getWebsitePageByDomain = function(domain, slug, callbacks) {
  var path = 'websites/domains/' + encodeURIComponent(domain);
  if (slug) {
    path += '/' + encodeURIComponent(slug);
  }

  this.send_(path, {
    method: 'GET',
    parse: function(data) {
      return [data['website'], data['page']];
    },
    callbacks: callbacks
  });
};


LKAPIClient.prototype.checkDomainCname = function(domain, callbacks) {
  this.send_('websites/check_domain_cname', {
    method: 'POST',
    parse: function(data) {
      return [data['correct'], data['error']];
    },
    params: {'domain': domain},
    callbacks: callbacks
  });
};


LKAPIClient.prototype.getExampleWebsite = function(itunesId, country, callbacks) {
  this.send_('websites/example', {
    method: 'POST',
    parse: function(data) {
      return [data['website']];
    },
    params: {'itunes_id': itunesId, 'country': country},
    callbacks: callbacks
  });
};


LKAPIClient.prototype.createWebsite = function(params, callbacks) {
  this.send_('websites', {
    method: 'POST',
    params: params,
    parse: function(data) {
      return [data['website']];
    },
    callbacks: callbacks
  });
};


LKAPIClient.prototype.editWebsite = function(websiteId, serializedForm, callbacks) {
  this.send_('websites/' + websiteId, {
    method: 'POST',
    params: serializedForm,
    parse: function(data) {
      return [data['website']];
    },
    callbacks: callbacks
  });
};



LKAPIClient.prototype.deleteWebsite = function(id, callbacks) {
  this.send_('websites/' + id + '/delete', {
    method: 'POST',
    callbacks: callbacks
  });
};


// SIMPLE DASH


LKAPIClient.prototype.addDashboardWithObject = function(object, callbacks) {
  this.send_('dashboards', {
    method: 'POST',
    json: object,
    parse: function(data) {
      var dashboard = data['dashboard'];
      return [dashboard];
    },
    callbacks: callbacks
  });
};


LKAPIClient.prototype.updateDashboard = function(id, updates, callbacks) {
  this.send_('dashboards/' + id, {
    method: 'POST',
    json: {'dashboard': updates},
    parse: function(data) {
      var dashboard = data['dashboard'];
      return [dashboard];
    },
    callbacks: callbacks
  });
};


LKAPIClient.prototype.dashboards = function(callbacks) {
  this.send_('dashboards', {
    method: 'GET',
    parse: function(data) {
      var dashboards = data['dashboards'];
      return [dashboards];
    },
    callbacks: callbacks
  });
};


LKAPIClient.prototype.dashboardWithId = function(dashId, callbacks) {
  this.send_('dashboards/' + dashId, {
    method: 'GET',
    parse: function(data) {
      var dashboard = data['dashboard'];
      return [dashboard];
    },
    callbacks: callbacks
  });
};


LKAPIClient.prototype.filledDashboardWithId = function(dashId, callbacks) {
  this.send_('dashboards/' + dashId + '/filled', {
    method: 'GET',
    parse: function(data) {
      var dashboard = data['dashboard'];
      return [dashboard];
    },
    callbacks: callbacks
  });
};


LKAPIClient.prototype.addMetricToDashboard = function(dashId, metricForm, callbacks) {
  this.send_('dashboards/' + dashId, {
    method: 'POST',
    json: {'metric': metricForm},
    parse: function(data) {
      var metric = data['metric'];
      return [metric];
    },
    callbacks: callbacks
  });
};


LKAPIClient.prototype.updateMetric = function(dashId, metricId, metricForm, callbacks) {
  this.send_('dashboards/' + dashId + '/' + metricId, {
    method: 'POST',
    params: metricForm,
    parse: function(data) {
      var metric = data['metric'];
      return [metric];
    },
    callbacks: callbacks
  });
};


LKAPIClient.prototype.deleteMetric = function(dashId, metricId,callbacks) {
  this.send_('dashboards/' + dashId + '/' + metricId + '/delete', {
    method: 'POST',
    callbacks: callbacks
  });
};


return new LKAPIClient();
