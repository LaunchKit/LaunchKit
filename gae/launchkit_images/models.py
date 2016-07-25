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

from google.appengine.ext import blobstore
from google.appengine.ext import db


class LKPhotoBlobstoreImage(db.Model):
  # These are keys into our PostgreSQL database, as horrifying as that is.
  table_name = db.StringProperty()
  db_id = db.IntegerProperty()

  # The actual image.
  image_blob = blobstore.BlobReferenceProperty()
  size_bytes = db.IntegerProperty()

  image_serving_url = db.StringProperty()

  @classmethod
  def key_for_table_id(cls, table_name, thing_id):
    return '%s:%d' % (table_name, thing_id)


class LKImageUpload(db.Model):
  # The uploaded image.
  image_blob = blobstore.BlobReferenceProperty()
  upload_time = db.DateTimeProperty(auto_now_add=True)

  image_width = db.IntegerProperty()
  image_height = db.IntegerProperty()
  image_format = db.StringProperty()
  image_metadata_json = db.TextProperty()
  image_serving_url = db.StringProperty()

  size_bytes = db.IntegerProperty()
