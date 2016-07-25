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
var object = skit.platform.object;
var navigation = skit.platform.navigation;
var urls = skit.platform.urls;

var productsObject = __module__.json;


module.exports = {
  findByUrl: function(url) {
    var parsed = urls.parse(url);
    return iter.find(productsObject['products'], function(product) {
      return parsed.path.indexOf(product.path) == 0;
    });
  },

  findById: function(id) {
    return iter.find(productsObject['products'], function(product) {
      return id == product.id;
    });
  },

  publicProducts: function() {
    return iter.map(productsObject['products'], function(product) {
      return object.copy(product);
    });
  }
};