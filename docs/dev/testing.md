# Testing Guidelines and Procedures

There are two levels of tests for the GREN Map DB Node:

1. Unit tests: Developer-written tests that confirm expected behavior of small code bites,
    and protect against regression errors.
2. Functional/UI tests: Tests written by a test engineer or software developer other than the
    one responsible for primary development on a feature or issue, testing larger chunks
    of functionality up to entire features, including the user interface.  These tests should treat
    the application almost as a "black box", other than the arrangement of preconditions before
    the test action is performed.

## Unit Tests

### Writing Unit Tests

Unit tests are placed in the "test" module of each Django app.
This module can be a test.py or tests.py file, or a test/tests directory with an __init__.py
and one or more test files within.

The pytest framework adds structure and style guidelines for unit tests.  Documentation:
https://docs.pytest.org/en/6.2.x/contents.html

See existing examples in the codebase for a quick start.

### Running Unit Tests

First, bring up the Docker Compose suite of services:

    docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

Second, execute the following to run unit tests:

    docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec -T app pytest

Handy tips to help save time when developing tests:

1. Adding the --reuse-db flag to the command to run tests can reduce overhead when re-running tests, with the caveat that any database changes between runs will not be reflected.

2. Narrowing the tests to only those for a single app is possible by naming it as an argument.

Putting these together:

    docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec -T app pytest --reuse-db <app_name>

## Functional/UI Tests

Functional testing should be used as an assurance that the software is acting as expected, without getting into specific lines of code, as unit tests do. Functional tests should describe what the system does by testing pieces of the system against their expected behavior.

### Writing Functional Tests

Functional tests are placed outside of the `/django` directory, in a directory off the main root called `/functional_test`.  This directory also contains a fixture directory `test_files`.

The pytest framework, chosen for additional features that the base python testing framework does not provide, adds structure and style guidelines for functional tests.  Documentation: https://docs.pytest.org/en/6.2.x/contents.html

See existing examples in the codebase for a quick start.

#### Support APIs

It is occasionally required to add/use REST APIs and RPCs written specifically for these tests, in order to set up preconditions for testing various actions.  These APIs are often inappropriate for production and should be marked and protected accordingly.

### Running Functional Tests

To execute the functional tests, create the .env.test file using env_example.test, and run the  provided integration_build file. This assumes no compose service containers are already up, and will bring them down afterwards.

    ./integration_build.sh

It is possible to run the commands in that script individually to save time when repeating runs.

## Load Tests

No load testing procedures or conventions have yet been established.  Please contact the development team to discuss.
