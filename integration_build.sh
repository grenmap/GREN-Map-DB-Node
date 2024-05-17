#!/bin/bash

fail_build() {
    clean_up
    if [ -n "$1" ]; then
        echo "Failing Integration Build at : $1"
    else
        echo "Failing Integration Build"
    fi
    exit 1  # proceed no further!
}

clean_up() {
    # Stop and remove all containers and images
    docker-compose -f docker-compose.yml -f docker-compose.dev.yml -f docker-compose.idp.yml -f docker-compose.test.node.yml -f docker-compose.test.selenium.yml -f docker-compose.test.yml down -v --rmi all

    # Remove all unused build cache
    docker builder prune -a -f
}

wait_for() {
    echo "Waiting for ready signal from $1... "
    while [[ $(docker inspect -f '{{.State.Health.Status}}' $1) != 'healthy' ]]
    do
        sleep 1
        echo "."
    done
    echo "$1 started"
}

echo "Run SSO builder ..."
chmod a+x ./config_sso.sh
. ./config_sso.sh

echo "Start Integration Build ..."

# Build dev environment
docker-compose -f docker-compose.yml -f docker-compose.dev.yml -f docker-compose.idp.yml build || fail_build "Build"

# Start dev environment
docker-compose -f docker-compose.yml -f docker-compose.dev.yml -f docker-compose.idp.yml up -d || fail_build "Deployment"

# Build and run functional tests in test container
docker-compose -f docker-compose.test.node.yml up -d --build || fail_build "Functional Test Node"

if [ "$(uname)" == "Darwin" ]
then
    # For Mac OS platform
    wait_for 'gren-map-db-node-app-1'
    wait_for 'gren-map-db-node-websp-1'
else
    wait_for 'gren-map-db-node_app_1'
    wait_for 'gren-map-db-node_websp_1'
fi

echo "Running unit test suite"
# Run unit tests in app container
docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec -T app pytest || fail_build "Unit Tests"

echo "Running functional test suite"
docker-compose -f docker-compose.test.selenium.yml up -d --build
echo "Waiting for Selenium Hub and Firefox to be ready before proceeding with test suite"
wait_for 'seleniumhub'
wait_for 'nodefirefox'
docker-compose -f docker-compose.test.yml build || fail_build "Build Test node"
docker-compose -f docker-compose.test.yml run test || fail_build "Functional Tests"

clean_up

echo "Done"
