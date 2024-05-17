#!/bin/bash

export SECRET_KEY=$(echo $RANDOM | md5sum | head -c 20)
export SQL_ENGINE=django.db.backends.sqlite3
python manage.py migrate
pytest --no-cov --tb=no
