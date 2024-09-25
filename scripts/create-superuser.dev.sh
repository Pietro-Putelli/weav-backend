#!/bin/sh

docker-compose -f docker-compose.dev.yml run --entrypoint="" app python backend/manage.py createsuperuser