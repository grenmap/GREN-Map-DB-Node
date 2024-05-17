#!/bin/bash

# check if flake8 is available
if ! command -v flake8 >/dev/null ; then
    echo "Please install flake8: https://flake8.pycqa.org"
    exit 1
fi

# run flake8
flake8 --config django/setup.cfg
readonly FLAKE8_STATUS=$?

# run unit tests
docker compose -f docker-compose.test.sqlite.yml up --build --exit-code-from app
readonly TEST_STATUS=$?

if [ "$FLAKE8_STATUS" -gt "0" ] && [ "$TEST_STATUS" -gt "0" ] ; then
    echo -n "Please fix the flake8 and the unit test errors "
    echo "before submitting a pull request."
    exit 1
fi

if [ "$FLAKE8_STATUS" -gt "0" ] ; then
    echo "Please fix the flake8 errors before submitting a pull request."
    exit 1
fi

if [ "$TEST_STATUS" -gt "0" ] ; then
    echo "Please fix the unit tests errors before submitting a pull request."
    exit 1
fi

echo "Flake8 and unit tests ok."
