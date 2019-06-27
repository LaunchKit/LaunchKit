#!/bin/sh
dev_appserver.py --log_level debug --host 0.0.0.0 --skip_sdk_update_check --port 9103 --admin_port 9104 --storage_path ./.dev_gae_storage gae &
go run devproxy.go 0.0.0.0:9102 localhost:9103