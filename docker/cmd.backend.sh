#!/bin/sh

# Fix secret key
sed -i "s|00000000000000000000000000000000|${SECRET_KEY}|" backend/settings.py

# Fix postgres settings
sed -i "s|'NAME': 'lk'|'NAME': '${POSTGRES_NAME}'|" backend/settings.py
sed -i "s|'USER': 'vagrant'|'USER': '${POSTGRES_USER}'|" backend/settings.py
sed -i "s|'PASSWORD': ''|'PASSWORD': '${POSTGRES_PASSWORD}'|" backend/settings.py
sed -i "s|'HOST': 'localhost'|'HOST': '${POSTGRES_HOST}'|" backend/settings.py

# sed -i "s|APP_ENGINE_PHOTOS_UPLOAD_BASE_PATH = \"http://localhost:9102\"|APP_ENGINE_PHOTOS_UPLOAD_BASE_PATH = \"http://gae:9102\"|" backend/settings.py

# Fix Redis settings
sed -i "s|redis://localhost:6379/0|${REDIS_URL}|" backend/settings.py

go run devproxy.go 0.0.0.0:9102 gae:9103 &

echo "Migrating database"
python manage.py migrate

celery worker -A backend.celery_app -Q \
  	celery,email,ingestion,archive,gae,slack,itunes,itunesux,itunesfetch,appstore,sessions \
  	-lINFO -B -Ofair --concurrency=1 &

echo "Starting server"
python manage.py runserver 0.0.0.0:${PORT}
