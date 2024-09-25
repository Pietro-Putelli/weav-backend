#!/bin/sh

until cd ../app/backend/
do
    echo "Waiting for server volume..."
done

uvicorn backend.asgi:application --host 0.0.0.0 --port 8000