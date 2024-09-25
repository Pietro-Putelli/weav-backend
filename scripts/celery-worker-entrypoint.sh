#!/bin/sh

until cd ../app/backend/
do
    echo "Waiting for server volume..."
done

celery -A backend worker -l info --concurrency 1 -B --scheduler django_celery_beat.schedulers:DatabaseScheduler