# Deployment

## Different Running Modes

The project can run in different modes: Development, Sandbox and Production.

The Production mode is the default.  There are examples of production deployment configurations in GitHub repositories, to help achieve quick and consistent deployments.

https://github.com/grenmap/GREN-Helm-Deployment-Example  
https://github.com/grenmap/GREN-Docker-Compose-Deployment-Example

- WARNING: Defaults shipped with the system or configured during the Quick Start are not considered production-ready, even in Production Mode.  Careful analysis of the configuration is recommended.  The example deployments above may be helpful.

## Running a Local Node for Evaluation or Development

Follow the [README Quick Start](https://github.com/grenmap/GREN-Map-DB-Node/blob/main/README.md#quick-start) for one or more local Nodes.  The configuration of that deployment should not be considered production-ready, for performance, security, and verbose logging reasons.

### Running in Development Mode

To enable this mode, set environment variable "DEVELOPMENT=1" in local environment or in file "env/.env.dev". To get more debug information, set environment variable "DEBUG=1".

Under this mode, when bringing the system up, it flushes the database, and imports the fixture from "visualization/fixtures/dev_origins.json" for development.

The project directory "django/" is mounted to the app container. Also another container is running parallel to collect the static files. Therefore, all the local changes will be reflected in the app container immediately.

Build all the Images
```
docker-compose -f docker-compose.yml -f docker-compose.dev.yml build --no-cache
```

To execute the project on Debug/Development mode, execute the following to bring the system up:
```
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

To rebuild all the images and bring the system up:
```
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

To bring the system down, as well as destroy the created volumes:
```
docker-compose -f docker-compose.yml -f docker-compose.dev.yml down -v
```

- NOTE: Without a system prune (see 'Troubleshooting' below), if the containers are brought down and then a new deployment build is performed with images, cache, and volumes left behind, then the database will be fully clean, including a lack of default Rules normally shipped with the application.

### Running in Production or Sandbox modes

Under these modes, the database will be preserved. When bring the system up, it cleans up and recollects all the static files. Accessing to APIs of "download_grenml" and "published_network_data" will require token.

Build all the Images
```
docker-compose build --no-cache
```

When running the project, execute the following:
```
docker-compose up -d
```

To run the project with rebuilding images:
```
docker-compose up -d --build
```

To bring the system down:
```
docker-compose down
```

#### Sandbox Mode

The Sandbox mode is almost the same as the Production mode. The only difference is that the Sandbox mode has the Polling app disabled; it does not communicate with other GREN Map DB Nodes. To enable the Sandbox mode, set an environment variable `SANDBOX=1` in local environment or in file "env/.env.prod".

## Troubleshooting and Routine Cleanup

Often when the containers are misconfigured or otherwise struggling to start, there will be two signs:
- attempts to visit the services in a web browser will indicate an error message stating that the containers are still starting
- the console output will indicate error messages, especially `nc: bad address 'app'`

In both of these cases, if bringing all containers down (see above) and purging them with a prune (see below) does not help, it is often due to a misconfiguration in one of the `env*` files.

### Corrupted Containers

Occasionally, especially during development, docker containers and images become corrupted or orphaned.
To clean this up, the following commands are available:

    docker system prune -a
    docker rmi $(docker images -a -q)

## Memory Constraints

There are two environment variables we can use to specify the amount of memory available for the containers running Django: `APP_MEMORY_LIMIT` for the app container and `TASK_RUNNER_MEMORY_LIMIT` for the task runner. Their default values are 150 megabytes.

Here's a command that starts a production deployment with 200 megabytes for app and task runner:
```sh
APP_MEMORY_LIMIT=200M TASK_RUNNER_MEMORY_LIMIT=200M docker-compose up
```

To verify the limits are set, use `docker stats`.
```sh
docker stats --format "{{.Name}}, {{.MemUsage}}" | grep -E "app|task_runner"
```

The output for the command above will be something like:
```
gren-map-db-node-task_runner-1, 115.9MiB / 200MiB
gren-map-db-node-app-1, 65.47MiB / 200MiB
```
