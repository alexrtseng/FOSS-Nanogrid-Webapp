#!/bin/zsh

# Activate your virtual environment
source /Users/alextseng/Desktop/Summer 2024/FOSS Nanogrid Webapp/.venv/bin/activate

# Navigate to your Django project directory
cd foss_nanogrid

# Start Celery worker
celery -A foss_nanogrid worker -l INFO &

# Start Celery beat (if you use it)
celery -A foss_nanogrid beat -l INFO --scheduler django_celery_beat.schedulers:DatabaseScheduler &

# Start Django development server
python manage.py runserver