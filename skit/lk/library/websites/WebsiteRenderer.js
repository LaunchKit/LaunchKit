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
var iter = skit.platform.iter;
var navigation = skit.platform.navigation;
var urls = skit.platform.urls;
var Handlebars = skit.thirdparty.handlebars;

var LKAPIClient = library.api.LKAPIClient;
var bootstrap = library.misc.bootstrap;
var fontawesome = library.misc.fontawesome;
var useragent = library.misc.useragent;
var templates = library.websites.templates;
var markdown = third_party.marked;

var meta = __module__.meta.html;
var html = __module__.html;
var pageHtml = __module__.page.html;


Handlebars.registerHelper('frameByDevice', function(screenshotPath, color, platform) {
  if (color == 'no') {
    return screenshotPath;
  }

  var phoneUrl;
  if (color == 'black') {
    phoneUrl = 'https://launchkit-io.imgix.net/devices/iPhone6Black.png';
  } else {
    phoneUrl = 'https://launchkit-io.imgix.net/devices/iPhone6White.png';
  }

  return urls.appendParams(phoneUrl, {
    'w': '750',
    'h': '1334',
    'mark': screenshotPath,
    'markh': '970',
    'markalign': 'center,middle'
  });
});

Handlebars.registerHelper('ifShowPlatform', function(website, targetPlatform, opts) {
  var userPlatform = useragent.findCompatibleMobilePlatform();
  if (targetPlatform == 'android' && website['playStoreId'] && userPlatform != 'iphone' && userPlatform != 'ipad') {
    return opts.fn(this);
  } else if (targetPlatform == 'ios' && website['itunesId'] && userPlatform != 'android') {
    return opts.fn(this);
  }
  return opts.inverse(this);
});

Handlebars.registerHelper('storeLink', function(website, targetPlatform, opts) {
  if (targetPlatform == 'android') {
    return urls.appendParams('https://play.google.com/store/apps/details', {
      'id': website['playStoreId']
    });
  }

  var proCampaignToken = (website['itunesCampaignToken']) ? website['itunesCampaignToken'] : null;
  var proProviderToken = (website['itunesProviderToken']) ? website['itunesProviderToken'] : null;

  var query = navigation.query();
  var itunesCampaignToken = query['ct'] || proCampaignToken;
  var itunesProviderToken = query['pt'] || proProviderToken;

  var params = {'mt': '8'};
  if (itunesCampaignToken) {
    params['ct'] = itunesCampaignToken;
  }
  if (itunesProviderToken) {
    params['pt'] = itunesProviderToken;
  }
  return urls.appendParams('https://itunes.apple.com/app/id' + website['itunesId'], params);
});

Handlebars.registerHelper('ifShowWaitingList', function(website, opts) {
  if (!website['playStoreId'] && !website['itunesId'] && website['waitingListLink']) {
    return opts.fn(this);
  } else {
    return opts.inverse(this);
  }
});

Handlebars.registerHelper('markdown', function(content) {
  return markdown(Handlebars.Utils.escapeExpression(content));
});

Handlebars.registerHelper('hasMenuItems', function(website, opts) {
  if (website.id == 'example' || website.blogLink || website.support || website.supportLink || website.customLink || website.loginLink) {
    return opts.fn(this);
  } else {
    return opts.inverse(this);
  }
});

Handlebars.registerHelper('subpathUrl', function(website, subpath) {
  var parsed = urls.parse(navigation.url());
  if (parsed && parsed.path && parsed.path.indexOf(website.id) > 0) {
    var parts = parsed.path.split(website.id);
    var prefix = parts[0];
    return prefix + website.id + '/' + subpath;
  }

  return '/' + subpath;
});

function WebsiteRenderer(website, opt_page) {
  this.website = website;
  this.page = opt_page || null;
  this.contentOnly = !!navigation.query()['content-only'];
  this.template = iter.find(templates.TEMPLATES, function(t) {
    return t.id == this.website['template'];
  }, this) || templates.TEMPLATES[0];

  this.website.homeUrl = '/';
  var host = navigation.host();
  if (host.match('localhost') || host.match('yourdomain.com')) {
    this.website.homeUrl = '/websites/'+this.website.id;
  }
}


WebsiteRenderer.prototype.title = function() {
  var pageTitle = this.website['appName'] + ' - ';

  if (this.page) {
    pageTitle += this.page['title'];
  } else {
    pageTitle += this.website['tagline'];
  }

  return pageTitle;
};


WebsiteRenderer.prototype.meta = function() {
  return meta({
    website: this.website
  });
};


WebsiteRenderer.prototype.body = function() {
  if (this.page) {
    return pageHtml({
      website: this.website,
      template: this.template,
      contentOnly: this.contentOnly,
      page: this.page
    });

  } else {
    return html({
      website: this.website,
      template: this.template
    });
  }
};


WebsiteRenderer.prototype.renderInIframe = function($iframe) {
  var iframe = $iframe.element || $iframe;
  var doc = iframe.contentWindow.document;
  var styleUrls = iter.map(dom.get('head').find('link[rel=stylesheet]'), function($style) {
    return $style.element.getAttribute('href');
  });
  var esc = Handlebars.Utils.escapeExpression;

  doc.open();
  doc.write('<!DOCTYPE HTML><html><head>');
  iter.forEach(styleUrls, function(url) {
    doc.write('<link rel="stylesheet" href="' + esc(url) + '">');
  });
  doc.write(this.meta());
  doc.write('</head><body>');
  doc.write(this.body());
  doc.write('</body>');
  doc.close();
};


module.exports = WebsiteRenderer;