#!/bin/bash

# Install dependencies
pip install -r requirements.txt

# Apply database migrations
python manage.py migrate --noinput

# Collect static files
python manage.py collectstatic --noinput

# Start the Django app with Gunicorn
gunicorn HubEducator.wsgi:application --bind 0.0.0.0:$PORT
