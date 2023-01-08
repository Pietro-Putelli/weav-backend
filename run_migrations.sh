#!/bin/bash

# Run Django makemigrations
docker-compose run app python manage.py makemigrations

# Run Django migrations
docker-compose run app python manage.py migrate