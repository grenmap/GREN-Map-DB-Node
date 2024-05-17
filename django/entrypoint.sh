#!/bin/bash

# Set up env from file: POSTGRES_PASSWORD_FILE and SECRET_KEY_FILE
# if POSTGRES_PASSWORD and SECRET_KEY don't exist
source file_env.sh

## Function to be called if any step of the deployment fails.
fail_deploy() {
    if [ -n "$1" ]; then
        echo "Failing deployment: $1"
    else
        echo "Failing deployment"
    fi
    exit 1  # proceed no further!
}

if [ "$DATABASE" = "postgres" ]
then
    echo "Waiting for postgres..."

    while ! nc -z $SQL_HOST $SQL_PORT; do
      sleep 0.1
    done

    echo "PostgreSQL started"
fi

# used in base_app/settings.py to compile django_q messages
export DJANGO_Q_LOCALE_PATH=$(find /usr/local/lib -name django_q)/locale

# TODO: Change to using an parameter argument to set a flag
# If the development flag is set, perform the development specific database actions
if [ ${DEVELOPMENT:-0} == 1 ]; then
  echo "For development configuration, run flush"
  python manage.py flush --no-input || fail_deploy "Flush Failed"
fi
python manage.py compilemessages || fail_deploy "Compile Messages Failed"
python manage.py makemigrations || fail_deploy "Make Migration Failed"
python manage.py migrate || fail_deploy "Migrate Failed"
echo "Loading collation rule model types"
python manage.py ruletypes
echo "Completed loading collation rule model types"

if [ ${DEVELOPMENT:-0} == 0 ]; then
  # In production the collection of static files is not done live, so it has to be run once
  echo "Collecting static files"
  python manage.py collectstatic --no-input --clear || fail_deploy "collectstatic Failed"
  echo "Collected static files"
fi

python manage.py initialisesettings || fail_deploy "initialisesettings Failed"

if [ ${SANDBOX:-0} != 1 ]; then
  # Setup polling if not in sandbox mode.
  python manage.py setup_polling || fail_deploy "setuppolling Failed"
fi

# Build the map visualization cache
python manage.py build_map_cache || fail_deploy "build map cache"

exec "$@"
