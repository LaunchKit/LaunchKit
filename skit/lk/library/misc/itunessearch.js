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
var urls = skit.platform.urls;


var COUNTRIES = [
  ['us', 'United States'],
  ['gb', 'United Kingdom'],
  ['au', 'Australia'],
  ['ag', 'Antigua and Barbuda'],
  ['ai', 'Anguilla'],
  ['al', 'Albania'],
  ['am', 'Armenia'],
  ['ao', 'Angola'],
  ['ar', 'Argentina'],
  ['at', 'Austria'],
  ['az', 'Azerbaijan'],
  ['bb', 'Barbados'],
  ['be', 'Belgium'],
  ['bf', 'Burkina Faso'],
  ['bg', 'Bulgaria'],
  ['bh', 'Bahrain'],
  ['bj', 'Benin'],
  ['bm', 'Bermuda'],
  ['bn', 'Brunei'],
  ['bo', 'Bolivia'],
  ['br', 'Brazil'],
  ['bs', 'Bahamas'],
  ['bt', 'Bhutan'],
  ['bw', 'Botswana'],
  ['by', 'Belarus'],
  ['bz', 'Belize'],
  ['ca', 'Canada'],
  ['cg', 'Republic Of Congo'],
  ['ch', 'Switzerland'],
  ['cl', 'Chile'],
  ['cn', 'China'],
  ['co', 'Colombia'],
  ['cr', 'Costa Rica'],
  ['cv', 'Cape Verde'],
  ['cy', 'Cyprus'],
  ['cz', 'Czech Republic'],
  ['de', 'Germany'],
  ['dk', 'Denmark'],
  ['dm', 'Dominica'],
  ['do', 'Dominican Republic'],
  ['dz', 'Algeria'],
  ['ec', 'Ecuador'],
  ['ee', 'Estonia'],
  ['eg', 'Egypt'],
  ['es', 'Spain'],
  ['fi', 'Finland'],
  ['fj', 'Fiji'],
  ['fm', 'Federated States Of Micronesia'],
  ['fr', 'France'],
  ['gd', 'Grenada'],
  ['gh', 'Ghana'],
  ['gm', 'Gambia'],
  ['gr', 'Greece'],
  ['gt', 'Guatemala'],
  ['gw', 'Guinea-Bissau'],
  ['gy', 'Guyana'],
  ['hk', 'Hong Kong'],
  ['hn', 'Honduras'],
  ['hr', 'Croatia'],
  ['hu', 'Hungary'],
  ['id', 'Indonesia'],
  ['ie', 'Ireland'],
  ['il', 'Israel'],
  ['in', 'India'],
  ['is', 'Iceland'],
  ['it', 'Italy'],
  ['jm', 'Jamaica'],
  ['jo', 'Jordan'],
  ['jp', 'Japan'],
  ['ke', 'Kenya'],
  ['kg', 'Kyrgyzstan'],
  ['kh', 'Cambodia'],
  ['kn', 'St. Kitts and Nevis'],
  ['kr', 'Republic Of Korea'],
  ['kw', 'Kuwait'],
  ['ky', 'Cayman Islands'],
  ['kz', 'Kazakstan'],
  ['la', 'Lao People’s Democratic Republic'],
  ['lb', 'Lebanon'],
  ['lc', 'St. Lucia'],
  ['lk', 'Sri Lanka'],
  ['lr', 'Liberia'],
  ['lt', 'Lithuania'],
  ['lu', 'Luxembourg'],
  ['lv', 'Latvia'],
  ['md', 'Republic Of Moldova'],
  ['mg', 'Madagascar'],
  ['mk', 'Macedonia'],
  ['ml', 'Mali'],
  ['mn', 'Mongolia'],
  ['mo', 'Macau'],
  ['mr', 'Mauritania'],
  ['ms', 'Montserrat'],
  ['mt', 'Malta'],
  ['mu', 'Mauritius'],
  ['mw', 'Malawi'],
  ['mx', 'Mexico'],
  ['my', 'Malaysia'],
  ['mz', 'Mozambique'],
  ['na', 'Namibia'],
  ['ne', 'Niger'],
  ['ng', 'Nigeria'],
  ['ni', 'Nicaragua'],
  ['nl', 'Netherlands'],
  ['no', 'Norway'],
  ['np', 'Nepal'],
  ['nz', 'New Zealand'],
  ['om', 'Oman'],
  ['pa', 'Panama'],
  ['pe', 'Peru'],
  ['pg', 'Papua New Guinea'],
  ['ph', 'Philippines'],
  ['pk', 'Pakistan'],
  ['pl', 'Poland'],
  ['pt', 'Portugal'],
  ['pw', 'Palau'],
  ['py', 'Paraguay'],
  ['qa', 'Qatar'],
  ['ro', 'Romania'],
  ['ru', 'Russia'],
  ['sa', 'Saudi Arabia'],
  ['sb', 'Solomon Islands'],
  ['sc', 'Seychelles'],
  ['se', 'Sweden'],
  ['sg', 'Singapore'],
  ['si', 'Slovenia'],
  ['sk', 'Slovakia'],
  ['sl', 'Sierra Leone'],
  ['sn', 'Senegal'],
  ['sr', 'Suriname'],
  ['st', 'Sao Tome and Principe'],
  ['sv', 'El Salvador'],
  ['sz', 'Swaziland'],
  ['tc', 'Turks and Caicos'],
  ['td', 'Chad'],
  ['th', 'Thailand'],
  ['tj', 'Tajikistan'],
  ['tm', 'Turkmenistan'],
  ['tn', 'Tunisia'],
  ['tr', 'Turkey'],
  ['tt', 'Trinidad and Tobago'],
  ['tw', 'Taiwan'],
  ['tz', 'Tanzania'],
  ['ua', 'Ukraine'],
  ['ug', 'Uganda'],
  ['uy', 'Uruguay'],
  ['uz', 'Uzbekistan'],
  ['vc', 'St. Vincent and The Grenadines'],
  ['ve', 'Venezuela'],
  ['vg', 'British Virgin Islands'],
  ['vn', 'Vietnam'],
  ['ye', 'Yemen'],
  ['za', 'South Africa'],
  ['zw', 'Zimbabwe'],
  ['ae', 'United Arab Emirates']
];

var COUNTRIES_BY_CODE = {};
COUNTRIES = iter.map(COUNTRIES, function(cn) {
  COUNTRIES_BY_CODE[cn[0]] = cn[1];
  return {name: cn[1], code: cn[0]};
});



function findApps(country, query, callback, context, opt_options) {
  var options = opt_options || {};

  var doneHandler = 'reviewsSearchCallback' + (+new Date());
  window[doneHandler] = function(resultsDict) {
    delete window[doneHandler];

    var rawResults = resultsDict['results'] || [];
    var results = iter.map(rawResults, function(raw) {
      // This is poorly mimicking the result returned by the LKAPIClient search call,
      // because I think that makes more sense in the template than randomly different stuff.
      return {
        iTunesId: raw['trackId'],
        name: raw['trackName'],
        icon: {
          small: raw['artworkUrl60']
        },
        developer: {
          name: raw['artistName']
        },
        screenshotUrls: raw['screenshotUrls']
      };
    });

    callback.call(context || window, query, results);
  };

  var entity = 'software';
  if (typeof options.ipad == 'undefined' || options.ipad) {
    entity += ',iPadSoftware';
  }
  if (typeof options.mac == 'undefined' || options.mac) {
    entity += ',macSoftware';
  }

  var script = document.createElement('script');
  script.src = urls.appendParams('https://itunes.apple.com/' + country + '/search', {
    'term': query,
    'entity': entity,
    'callback': doneHandler
  });
  script.className = 'itunessearch-script';

  iter.forEach(dom.find('script.itunessearch-script'), function($s) {
    $s.remove();
  });

  dom.get('head').append(script);
}


module.exports = {
  COUNTRIES: COUNTRIES,
  COUNTRIES_BY_CODE: COUNTRIES_BY_CODE,
  findApps: findApps
};