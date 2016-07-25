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
var string = skit.platform.string;
var urls = skit.platform.urls;
var Handlebars = skit.thirdparty.handlebars;

var moment = third_party.moment;
var twemoji = third_party.twemoji;

var SHORT_ISO_DATE_FORMAT = 'MMM D, YYYY';
var SHORT_DATE_FORMAT = 'M/DD/YY h:mm a';
var SHORT_DATE_FORMAT_NOTIME = 'M/DD/YY';
var LONG_DATE_FORMAT = 'MMMM Do YYYY, h:mm a';
var LONG_DATE_FORMAT_NOTIME = 'MMMM D, YYYY';



function prettyPrintNumber(value, opt_decimalDigits) {
  // ensure value is numeric.
  if (!value) {
    return '0' + (opt_decimalDigits ? '.000000000000'.substring(0, opt_decimalDigits + 1) : '');
  }

  var intValue = Math.floor(value);
  var decimal = value - intValue;

  if (opt_decimalDigits) {
    var tenner = Math.pow(10, opt_decimalDigits);
    decimal = (Math.round(value * tenner) / tenner) - Math.floor(value);
  }

  var formatted = '';
  while (intValue > 0) {
    var remainder = (intValue % 1000);
    intValue = Math.floor(intValue / 1000);
    if (intValue > 0) {
      if (remainder < 10) {
        remainder = '00' + remainder;
      } else if (remainder < 100) {
        remainder = '0' + remainder;
      }
    }
    formatted = (remainder + (formatted ? ',' : '')) + formatted;
  }

  if (decimal) {
    // add ".47"
    var decimalStr = decimal + '';
    if (opt_decimalDigits) {
      var end = (1 + opt_decimalDigits + 1);
      decimalStr = decimalStr.substring(1, end);
    } else {
      decimalStr = decimalStr.substring(1);
    }
    formatted += decimalStr;
  }

  return formatted;
}


//
// COMMON TEMPLATE HELPERS
//

function dateFromNumber(date) {
  // TODO(Taylor): Remove crazy date string parsing crap sometime.
  if (date && date.match && date.match(/^\d{4}-\d{2}-\d{2}T.+Z$/)) {
    return new Date(Date.parse(date));
  }

  // probably a non-ms unix timestamp
  if (date < 1577779200) {
    date *= 1000;
  }
  date = new Date(date);
  return date;
}

function breakLongWords(sanitized) {
  return sanitized.replace(/\w{20}/g, function(s) {
    return s + '&shy;';
  });
}


function zeroPad(n, width) {
  n = '' + n;
  while (n.length < width) {
    n = '0' + n;
  }
  return n;
}


var ALL_HELPERS = {
  json: function(arg, opt_pretty) {
    // + here forces numeric. default last argument is handlebars context obj,
    // so is truthy if not forced to evaluate as a number first.
    return JSON.stringify(arg, null, +opt_pretty ? 2 : null).replace(/[<>'&\u2028\u2029]/g, function(char) {
      var str = char.charCodeAt(0).toString(16);
      return '\\u0000'.substring(0, 2 + (4 - str.length)) + str;
    });
  },

  spaceless: function(options) {
    var content = options.fn(this);
    return content.replace(/>\s+</mg, '><');
  },

  pluralize: function(number, single, plural) {
    return (number === 1) ? single : plural;
  },

  timeFromNow: function(context, block) {
    if (!context) {
      return 'Never';
    }

    var date = dateFromNumber(context);
    var now = +(new Date());
    if (now - date < (2 * 60 * 1000)) {
      return 'Just now';
    }

    return moment(date).fromNow();
  },

  shortISODate: function(isoString) {
    return moment(isoString).format(SHORT_ISO_DATE_FORMAT);
  },

  shortDate: function(context) {
    var date = dateFromNumber(context);
    return moment(date).format(SHORT_DATE_FORMAT);
  },

  shortDateNoTime: function(context) {
    var date = dateFromNumber(context);
    return moment(date).format(SHORT_DATE_FORMAT_NOTIME);
  },

  longDate: function(context) {
    var date = dateFromNumber(context);
    return moment(date).format(LONG_DATE_FORMAT);
  },

  longDateNoTime: function(context) {
    var date = dateFromNumber(context);
    return moment(date).format(LONG_DATE_FORMAT_NOTIME);
  },

  formatNumber: prettyPrintNumber,

  formatCurrency: function(amount) {
    return '$' + prettyPrintNumber(amount, 2);
  },

  centsToDollars: function(amount) {
    var isNegative = (amount < 0) ? '-' : '';

    if (isNegative == '-') {
      amount *= -1;
    }
    return isNegative + '$' + prettyPrintNumber(amount / 100, 2);
  },

  formatDuration: function(totalSeconds) {
    // Round up from zero so the smallest amount
    // we have is one second in the case of partial seconds.
    totalSeconds = Math.ceil(totalSeconds || 0);

    var HOUR = 60 * 60;
    var seconds = Math.floor(totalSeconds % 60);
    var hours = Math.floor(totalSeconds / HOUR);
    var minutes = Math.floor((totalSeconds - (hours * HOUR)) / 60);

    var parts = [];
    if (hours) {
      parts.push(hours + 'h');
    }
    if (minutes && hours < 10) {
      parts.push(minutes + 'm');
    }
    // not if (seconds) because seconds might be 0, we want "0s" to show up.
    if (hours < 1 && minutes < 10) {
      parts.push(seconds + 's');
    }

    // non-breaking space (&nbsp;):
    return parts.join('\u00A0');
  },

  bodyText: function(context, block) {
    var graphs = (context || '').split(/[\n\r]{2}/);
    var result = [];
    iter.forEach(graphs, function(substr) {
      result.push('<p>');
      var sanitized = breakLongWords(Handlebars.Utils.escapeExpression(substr).replace('\n', '<br>'));
      result.push(sanitized);
      result.push('</p>');
    });
    return new Handlebars.SafeString(result.join(''));
  },

  brBodyText: function(context, block) {
    var substrings = (context || '').split(/\n/);
    var result = [];
    iter.forEach(substrings, function(substr) {
      result.push(Handlebars.Utils.escapeExpression(substr));
    });
    return new Handlebars.SafeString(result.join('<br>'));
  },

  join: function(items, joinStr, options) {
    var rendered = [];
    iter.forEach(items || [], function(item) {
      var html = string.trim(options.fn(item));
      rendered.push(html);
    });
    return new Handlebars.SafeString(rendered.join(joinStr));
  },

  eachGroup: function(list, groupSize, opts) {
    var parts = [];
    while (list.length) {
      var group = list.slice(0, groupSize);
      list = list.slice(groupSize, list.length);

      parts.push(opts.fn(group));
    }
    return parts.join('');
  },

  isSet: function(a, b, opts) {
    if (b && b[a]) {
      return opts.fn(this);
    } else {
      return opts.inverse(this);
    }
  },

  ifEqual: function(a, b, opts) {
    if (a == b) {
      return opts.fn(this);
    } else {
      return opts.inverse(this);
    }
  },

  ifPositive: function(a, opts) {
    if (a > 0) {
      return opts.fn(this);
    } else {
      return opts.inverse(this);
    }
  },

  ifNonnegative: function(a, opts) {
    if (a >= 0) {
      return opts.fn(this);
    } else {
      return opts.inverse(this);
    }
  },

  ifGreater: function(a, b, opts) {
    if (a > b) {
      return opts.fn(this);
    } else {
      return opts.inverse(this);
    }
  },

  emojiHtml:  function(options) {
    var content = options.fn(this);
    // TODO(Taylor): Remove when twemoji supports unicode skin modifiers.
    content = content.replace(/\ud83c[\udffb-\udfff]/g, '');
    return new Handlebars.SafeString(twemoji.parse(content));
  },

  ifPathStartsWith: function(path, opts) {
    if (urls.parse(navigation.url()).path.indexOf(path) == 0) {
      return opts.fn(this);
    } else {
      return opts.inverse(this);
    }
  },

  ifPathContains: function(path, opts) {
    if (urls.parse(navigation.url()).path.indexOf(path) != -1) {
      return opts.fn(this);
    } else {
      return opts.inverse(this);
    }
  },

  toLowerCase: function(str) {
    return str.toLowerCase();
  },

  sdkUserName: function(sdkUser) {
    return (sdkUser ? sdkUser.name || sdkUser.email || sdkUser.uniqueId : null) || 'Anonymous';
  }

};

var exports = {
  register: function(name) {
    Handlebars.registerHelper(name, ALL_HELPERS[name]);
  },

  registerAll: function() {
    for (var helperName in ALL_HELPERS) {
      Handlebars.registerHelper(helperName, ALL_HELPERS[helperName]);
    }
  }
};

for (var helperName in ALL_HELPERS) {
  exports[helperName] = ALL_HELPERS[helperName];
}

module.exports = exports;
