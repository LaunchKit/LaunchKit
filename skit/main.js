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

var crypto = require('crypto');
var path = require('path');
var util = require('util');

var skit = require('skit');
var minimist = require('minimist');
var transformer = require('./JSXTransformer');
var scriptresource = skit.scriptresource;
var JavaScriptResource = scriptresource.JavaScriptResource;

var settings = require('./settings');


var PUBLIC_PORT;
var API_HOST;

var COOKIE_NAME = 'lkauth';
var COOKIE_ALGO = 'aes-256-cbc';
var COOKIE_KEY = settings.COOKIE_KEY;

var COOKIE_AGE_MS = 14 * 24 * 60 * 60 * 1000;
var MAX_COOKIE_AGE_MS = 30 * 24 * 60 * 60 * 1000;
var IV_LENGTH = 16;


function setEncryptedCookie(res, name, value) {
  if (!value) {
    res.setCookie(name, undefined);
    return;
  }

  var iv = crypto.randomBytes(16).toString('binary');
  var cipher = crypto.createCipheriv(COOKIE_ALGO, COOKIE_KEY, iv);
  var timedValue = +(new Date()) + ':' + value;

  var encrypted = cipher.update(timedValue, 'utf8', 'binary');
  encrypted += cipher.final('binary');
  encrypted = (new Buffer(iv + encrypted, 'binary')).toString('base64');

  res.setCookie(name, encrypted, {httpOnly: true, maxAge: COOKIE_AGE_MS});
}


function getEncryptedCookie(req, name) {
  var value = req.getCookie(name);
  if (!value) {
    return null;
  }
  return decryptCookieValue(value);
}


function decryptCookieValue(value) {
  value = (new Buffer(value, 'base64')).toString('binary');

  var iv = value.substring(0, IV_LENGTH);
  if (iv.length != IV_LENGTH) {
    return null;
  }
  value = value.slice(IV_LENGTH);

  var decipher = crypto.createDecipheriv(COOKIE_ALGO, COOKIE_KEY, iv);
  var decrypted;
  try {
    decrypted = decipher.update(value, 'binary', 'binary');
    decrypted += decipher.final('binary');
    decrypted = (new Buffer(decrypted, 'binary')).toString('utf8');
  } catch (e) {
    return null;
  }

  var parts = decrypted.split(':');
  var now = +(new Date());
  var cookieTime = +parts[0];
  if (cookieTime > now - MAX_COOKIE_AGE_MS && cookieTime < now) {
    return parts.slice(1).join(':');
  }

  return null;
}


function modifyRequest(proxyRequest, apiRequest) {
  ['x-forwarded-for', 'x-forwarded-host', 'x-forwarded-proto', 'referer'].forEach(function(header) {
    apiRequest.headers[header] = proxyRequest.headers[header];
  });

  apiRequest.url = API_HOST + 'v1/' + apiRequest.url;

  var oauthToken = getEncryptedCookie(proxyRequest, COOKIE_NAME);
  if (!oauthToken) {
    // Fall back to "raw" cookie possibly provided by the iPhone client.
    oauthToken = proxyRequest.getCookie('lkauth-raw') || null;
  }

  if (oauthToken) {
    apiRequest.headers['Authorization'] = 'Bearer ' + oauthToken;
  }

  if (apiRequest.method == 'POST') {
    if (apiRequest.url.indexOf('/oauth2/token') > 0) {
      if (apiRequest.body) {
        apiRequest.body += '&';
      } else {
        apiRequest.body = '';
      }
      apiRequest.body += 'client_id=launchkit-skit&client_secret=5ZP672EiPfWHLsoDPitlcTE3CKQnE4ynVjgNKBx4EQNoi';
    }
  }
}
function modifyResponse(apiRequest, apiResponse, proxyResponse) {
  var invalidCookie = apiResponse.status == 401;
  if (!invalidCookie) {
    var value = proxyResponse.getCookie(COOKIE_NAME);
    if (value && !decryptCookieValue(value)) {
      invalidCookie = true;
    }
  }

  if (invalidCookie || apiRequest.url.indexOf('/logout') > 0) {
    setEncryptedCookie(proxyResponse, COOKIE_NAME, null);
  } else if (apiRequest.url.indexOf('/oauth2/token') > 0) {
    var body = apiResponse.body || {};
    if (body['token_type'] === 'Bearer' && body['access_token']) {
      setEncryptedCookie(proxyResponse, COOKIE_NAME, body['access_token']);
    }
  }
}

var LAUNCHKIT_IO_PUBLIC = 'public';
var HOSTED_PUBLIC = 'public_hosted';

var args = minimist(process.argv.slice(2), {
  default: {
    'port': 9100,
    'api-host': settings.API_URL,
    'package': 'lk',
  },
  string: ['optimize', 'api-host', 'package', 'optimize-static-root',],
  boolean: ['debug', 'use-alias-map', 'public-hosted',],
});


PUBLIC_PORT = args['port'];
API_HOST = args['api-host'];

var pkg = args['package'];


var options = {};
options.publicRoot = args['public-hosted'] ? HOSTED_PUBLIC : LAUNCHKIT_IO_PUBLIC;


var REACT_DEPENDENCY_PATH;
var REACT_DEPENDENCY_DOM_PATH;
if (args['debug']) {
  options.debug = true;

  REACT_DEPENDENCY_PATH = 'third_party.react_dev.React';
  REACT_DOM_DEPENDENCY_PATH = 'third_party.react_dev.ReactDOM';
} else {
  options.debug = false;

  REACT_DEPENDENCY_PATH = 'third_party.react_prod.React';
  REACT_DOM_DEPENDENCY_PATH = 'third_party.react_prod.ReactDOM';
}

var ALIAS_MAP_PATH = '__' + options.publicRoot + '_alias_map__.json';
if (args['use-alias-map']) {
  options.aliasMap = ALIAS_MAP_PATH;
}

options.redirectWithTrailingSlashes = true;

options.env = {
  'appEngineHost': settings.APP_ENGINE_HOST,
};


if (options.publicRoot == LAUNCHKIT_IO_PUBLIC) {
  options.bundleConfiguration = [
    {
      name: 'base',
      paths: [
        '/',
        '/login',
        '/signup',
        '/dashboard',
      ],
      modules: [
        'library.controllers.Dashboard',
        'library.controllers.onboarding.iTunesAppSearch',
        'library.misc',
        'library.overlays',
        'library.tasks',
        'library.uploads',
        'library.api.LKAnalyticsAPIClient',
      ]
    },
    {
      name: 'react',
      modules: [
        // the main client library
        REACT_DEPENDENCY_PATH,
        REACT_DOM_DEPENDENCY_PATH,
        'third_party.ReactDOMServer',
        // shared components used throughout
        'library.react.components',
        'library.react.lib',
      ],
      options: {
        // most of this file is already minified, and minification here
        // takes goddam forever on reactcompiled.
        uglifyOptions: {compress: false}
      }
    },
    {
      name: 'account',
      paths: [
        '/account/*',
      ]
    },
    {
      name: 'reviews',
      paths: [
        '/reviews*',
      ]
    },
    {
      name: 'screenshots',
      paths: [
        '/screenshots/*',
      ]
    },
    {
      name: 'sales',
      paths: [
        '/sales/*',
      ]
    },
    {
      name: 'websites',
      paths: [
        '/websites/*',
      ]
    },
    {
      name: 'super-users',
      paths: [
        '/users/*',
      ]
    },
    {
      name: 'config',
      paths: [
        '/config/*',
      ]
    }
  ];
} else if (options.publicRoot == HOSTED_PUBLIC) {
  options.bundleConfiguration = [
    {
      name: 'websites-public',
      paths: [
        '/*',
      ]
    }
  ];
}

/**
 * This is a custom handler for loading / preprocessing .jsx files using the
 * react JSXTranformer. This makes .jsx files work in skit.
 */
var ReactResource = function(filePath, modulePath, source) {
  source = transformer.transform(source, {harmony: true}).code;
  JavaScriptResource.call(this, filePath, modulePath, source);
};
util.inherits(ReactResource, JavaScriptResource);

ReactResource.REACT_DEPENDENCY_PATH = REACT_DEPENDENCY_PATH;
ReactResource.REACT_DOM_DEPENDENCY_PATH = REACT_DOM_DEPENDENCY_PATH;

ReactResource.prototype.findDependencyPaths_ = function() {
  var deps = JavaScriptResource.prototype.findDependencyPaths_.apply(this, arguments);
  deps.unshift(ReactResource.REACT_DEPENDENCY_PATH);
  deps.unshift(ReactResource.REACT_DOM_DEPENDENCY_PATH);
  return deps;
};

ReactResource.prototype.aliasForDependencyPath = function(dependencyPath) {
  if (dependencyPath == ReactResource.REACT_DEPENDENCY_PATH) {
    return 'React';
  }
  if (dependencyPath == ReactResource.REACT_DOM_DEPENDENCY_PATH) {
    return 'ReactDOM';
  }
  return JavaScriptResource.prototype.aliasForDependencyPath.call(this, dependencyPath);
};

// This sets the .jsx extension to be handled by this JavaScriptResource subtype.
scriptresource.setResourceWrapper('.jsx', ReactResource);


var server = new skit.SkitServer(path.join(__dirname, pkg), options);
server.registerProxy('lk', modifyRequest, modifyResponse);

var optimizedPackage = args['optimize'];
if (optimizedPackage) {
  skit.optimizeServer(server, optimizedPackage, {
    aliasMap: ALIAS_MAP_PATH,
    staticRoot: args['optimize-static-root'],
  });
  return;
}

server.listen(PUBLIC_PORT);
console.log('Skit listening on port:', PUBLIC_PORT);
