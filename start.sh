#!/bin/bash

# Install dependencies
pip install -r requirements.txt

# Make sure Gunicorn is installed
pip install gunicorn

# Apply migrations
python manage.py migrate --noinput

# Collect static files
python manage.py collectstatic --noinput

# Start the app
gunicorn HubEducator.wsgi:application --bind 0.0.0.0:$PORT
