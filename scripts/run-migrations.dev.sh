#!/bin/sh

docker-compose -f docker-compose.dev.yml run --entrypoint="" app python backend/manage.py makemigrations

docker-compose -f docker-compose.dev.yml run --entrypoint="" app python backend/manage.py migrate