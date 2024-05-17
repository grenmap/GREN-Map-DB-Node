#!/bin/bash

# Set up env from file: POSTGRES_PASSWORD_FILE and SECRET_KEY_FILE
# if POSTGRES_PASSWORD and SECRET_KEY don't exist
source file_env.sh

echo "Waiting for app server..."

while ! nc -z 'app' 8080; do
  sleep 0.1
done

echo "app container started"
exec "$@"
