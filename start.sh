#!/bin/bash

# Install dependencies
pip install -r requirements.txt

pip install gunicorn
# Apply migrations
python manage.py migrate --noinput

# Collect static files
python manage.py collectstatic --noinput

# Start the Django app on the port Railway provides
python manage.py runserver 0.0.0.0:$PORT
