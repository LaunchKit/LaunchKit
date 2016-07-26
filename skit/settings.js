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


module.exports = {
	// This is the encryption key for the LK server cookies.
	// Change this to a hex value of the same length.
	COOKIE_KEY: '00000000000000000000000000000000',

	// The path to the LaunchKit API server, from the perspective of the
	// node.js webserver.
	API_URL: 'http://localhost:9101/',

	// This should be the same as settings.py's APP_ENGINE_HOST value,
	// and should only be changed in the case that you are modifying
	// hosting configuration.
	// (This is passed through to client-side JavaScript in order to figure
	// out where images should be uploaded.)
	APP_ENGINE_HOST: 'http://localhost:9102/',
};