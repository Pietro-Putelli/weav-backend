#!/bin/bash

# Run Django makemigrations
docker-compose run app python manage.py makemigrations $1

# Run Django migrations
docker-compose run app python manage.py migrate $1