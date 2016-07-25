#!/usr/bin/env python

#
# Copyright 2016 Cluster Labs, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import os
import webapp2

from launchkit_images.blobinternalhandlers import *
from launchkit_images.blobpublichandlers import *


software = os.getenv('SERVER_SOFTWARE')
DEBUG   = software and ('Dev' in software)


app = webapp2.WSGIApplication([
  (PUBLIC_BLOBSTORE_UPLOAD_HANDLER_PATH, PublicBlobstoreFileUploadHandler),

  (r'/image_upload', PublicPostbodyUploadHandler),
  (r'/image_fetch', FetchRemoteImageUploadHandler),

  (r'/assign_uploaded_image', AssignUploadedImageHandler),
  (r'/get_uploaded_image_urls', GetUploadedImageUrlsHandler),
  (r'/(\w+)/(\d+)', ImageInfoHandler),

  (r'/.*', PublicRedirectHandler),
], debug=DEBUG)
