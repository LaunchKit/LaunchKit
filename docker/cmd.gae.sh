#!/bin/sh
/usr/local/google_appengine/dev_appserver.py --log_level debug --skip_sdk_update_check --port ${PORT} --admin_port ${ADMIN_PORT} --storage_path ./.dev_gae_storage .
