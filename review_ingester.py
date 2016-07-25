#!/usr/bin/env python2.7
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

import logging
import os
import signal
import time

import django

from backend.lk.logic import appstore_review_ingestion

# This sets up logging.
django.setup()


SHUTDOWN = False

def handle_shutdown_signal(signum, frame):
  logging.info('Received signal %s, shutting down...', signum)
  global SHUTDOWN
  SHUTDOWN = True


def main():
  logging.info('Looking for reviews to ingest...')

  ingested_count = 0

  while not SHUTDOWN:
    for app, country in appstore_review_ingestion.apps_countries_to_ingest(30):
      appstore_review_ingestion.ingest_app(app, country)
      ingested_count += 1

      if SHUTDOWN:
        break

    if ingested_count >= 25:
      logging.info('Ingested reviews for %d app(s)...', ingested_count)
      ingested_count = 0

    else:
      # If the queue is empty, chill out.
      time.sleep(1.0)


if __name__ == '__main__':
  signal.signal(signal.SIGABRT, handle_shutdown_signal)
  signal.signal(signal.SIGINT, handle_shutdown_signal)
  signal.signal(signal.SIGTERM, handle_shutdown_signal)

  main()
