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
var navigation = skit.platform.navigation;
var urls = skit.platform.urls;

var LKAPIClient = library.api.LKAPIClient;


var ONE_MINUTE = 60 * 1000;
var NUM_CACHED_ITEMS = 50;
var CACHED_HOSTS = [];


function loadForCurrentDomainSlug(slug, done, ctx) {
  var domain = (navigation.host() || '').split(':')[0].substring(0, 64);
  if (!domain) {
    done.call(ctx, '', null, null);
    return;
  }

  var now = +(new Date());

  var foundHostIndex = iter.indexOf(CACHED_HOSTS, function(nfh) {
    return nfh.domain == domain && nfh.slug == slug;
  });

  if (foundHostIndex >= 0) {
    var nfh = CACHED_HOSTS[foundHostIndex];
    CACHED_HOSTS.splice(foundHostIndex, 1);
    if (nfh.time > now - ONE_MINUTE) {
      // LRU-ish.
      CACHED_HOSTS.unshift(nfh);
      CACHED_HOSTS.splice(50);

      done.call(ctx, domain, nfh.website, nfh.page);
      return;
    }
  }

  var foundHost = {
    time: now,
    domain: domain,
    slug: slug
  };

  LKAPIClient.getWebsitePageByDomain(domain, slug, {
    onSuccess: function(loadedWebsite, loadedPage) {
      foundHost.website = loadedWebsite;
      foundHost.page = loadedPage;
    },
    onError: function() {
      navigation.notFound();
    },
    onComplete: function() {
      CACHED_HOSTS.unshift(foundHost);
      CACHED_HOSTS.splice(50);
      done.call(ctx, domain, foundHost.website, foundHost.page);
    }
  });
}


module.exports = {loadForCurrentDomainSlug: loadForCurrentDomainSlug};