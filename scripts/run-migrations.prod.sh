#!/bin/sh

docker-compose run --entrypoint="" app python backend/manage.py makemigrations

docker-compose run --entrypoint="" app python backend/manage.py migrate