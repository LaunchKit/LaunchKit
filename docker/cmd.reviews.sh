#!/bin/sh

# Fix secret key
sed -i "s|00000000000000000000000000000000|${SECRET_KEY}|" backend/settings.py

# Fix postgres settings
sed -i "s|'NAME': 'lk'|'NAME': '${POSTGRES_NAME}'|" backend/settings.py
sed -i "s|'USER': 'vagrant'|'USER': '${POSTGRES_USER}'|" backend/settings.py
sed -i "s|'PASSWORD': ''|'PASSWORD': '${POSTGRES_PASSWORD}'|" backend/settings.py
sed -i "s|'HOST': 'localhost'|'HOST': '${POSTGRES_HOST}'|" backend/settings.py

# Fix Redis settings
sed -i "s|redis://localhost:6379/0|${REDIS_URL}|" backend/settings.py

python review_ingester.py
