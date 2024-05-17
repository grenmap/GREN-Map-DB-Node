#!/bin/bash

fail_build() {
    if [ -n "$1" ]; then
        echo "Functional test build failed at: $1"
    else
        echo "Functional test build failed."
    fi
    exit 1
}

wait_for() {
    while [[ $(docker inspect -f '{{.State.Health.Status}}' $1) != 'healthy' ]]
    do
        sleep 1
        echo "Waiting for ready signal from $1... "
    done
    echo "$1 started"
}

clean_up() {
    # Stop and remove all containers and images
    docker-compose -f docker-compose.yml -f docker-compose.dev.yml -f docker-compose.idp.yml -f docker-compose.test.node.yml -f docker-compose.test.selenium.yml -f docker-compose.test.yml down --remove-orphans -v --rmi all

    # Remove all unused build cache
    docker builder prune -a -f

    # Remove all dangling images
    docker image prune -f
}

set_up() {

  echo "Run SSO builder ..."
  chmod a+x ./config_sso.sh
  . ./config_sso.sh

  echo "Starting functional test system build..."

  # Build dev environment
  docker-compose -f docker-compose.yml -f docker-compose.dev.yml -f docker-compose.idp.yml build || fail_build "Build"

  # Start dev environment
  docker-compose -f docker-compose.yml -f docker-compose.dev.yml -f docker-compose.idp.yml up -d || fail_build "Deployment"

  # Build functional tests container
  docker-compose -f docker-compose.test.node.yml up -d --build || fail_build "Functional Test Node"

  # Wait for the above containers to be ready
  if docker inspect -f '{{.State.Health.Status}}' gren-map-db-node-app-1; then
      wait_for 'gren-map-db-node-app-1'
      wait_for 'gren-map-db-node-websp-1'
  else
      wait_for 'gren-map-db-node_app_1'
      wait_for 'gren-map-db-node_websp_1'
  fi

  # Build Selenium containers and wait for them to be ready
  docker-compose -f docker-compose.test.selenium.yml up -d --build
  echo "Waiting for Selenium Hub and Firefox to be ready before proceeding with test suite"
  wait_for 'seleniumhub'
  wait_for 'nodefirefox'

  docker-compose -f docker-compose.test.yml build || fail_build "Build Test node"

  echo "Functional test system is ready."

}

run() {

  echo "Running functional test suite..."
  docker-compose -f docker-compose.test.yml run test || fail_build "Functional Tests"

}

if [[ "$1" == "setup" ]]; then
  set_up
elif [[ "$1" == "run" ]]; then
  run
elif [[ "$1" == "cleanup" ]]; then
  clean_up
elif [ $# -eq 0 ]; then
  echo "This script can be split into three sections by providing an argument: setup, run, or cleanup."
  set_up
  run
  clean_up
else
  echo "This script can be split into three sections by providing an argument: setup, run, or cleanup."
fi
