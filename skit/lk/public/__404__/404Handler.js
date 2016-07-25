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
var navigation = skit.platform.navigation;

var FloatingBox = library.controllers.FloatingBox;

var html = __module__.html;


module.exports = Controller.create(FloatingBox, {
  dontLoadUser: true,

  __title__: function() {
    return 'Not Found';
  },

  __body__: function() {
    return html();
  }
});