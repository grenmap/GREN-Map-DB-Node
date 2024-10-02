# GREN Map Database Node

## Overview

The Global Research and Education Network (GREN) is a "network of networks" that links great minds to each other, and to technologies, research facilities, and data, enabling global research collaborations and education support.

The [GREN Map](https://github.com/grenmap) is a database of this connectivity, to be used for visualizing it in both static and interactive displays.  It consists of a hierarchical distributed database: each Research and Education Network (REN) will maintain a database node of their own, and also aggregate the data from nodes for the smaller networks that it connects, on a regular polling interval.  Ultimately, data will percolate up to a central node for the entire globe.

This repository provides the code for an instance representing a single node in the hierarchy described above.

## Requirements

This container requires Docker and Docker Compose.

* [Docker Desktop for Windows](https://docs.docker.com/desktop/install/mac-install/)
* [Docker Desktop for Mac OS X](https://docs.docker.com/desktop/install/windows-install/)
* [Docker Desktop for Linux](https://docs.docker.com/desktop/install/linux-install/)

Production deployment of this software requires a Shibboleth-based single sign-on identity provider ("IdP") to authenticate users.  For local development or evaluation purposes, a local IdP container (included) may be used.  The Quick Start instructions below include this IdP container.

## Quick Start

This Quick Start details how to bootstrap this application for evaluation or development.

Production deployment instructions and examples are found in a separate repository.  Contact the application developers for more information if required.

### Environment Files

After pulling the code from the repository, the first step is to create an environment file that will affect how the containers are configured.  There are some examples in the repository to serve as starting points.  Copy the file
    - env/env_example.dev
to a new file
    - env/.env.dev
and replace/insert values for the keys listed below with your own.

- **SECRET_KEY** - Can be any value, should be random
    - The following command will generate a suitable random key if Python 3 is installed:
      ```sh
      python3 -c "import secrets; print(secrets.token_urlsafe(50))"
      ```
- **DJANGO_ALLOWED_HOSTS** - The list of names to which this server will respond (defaults sufficient for local/dev installations; add/replace for public access)
- **CSRF_TRUSTED_ORIGINS** - The list of URLs to which this server will respond; each URL should have a scheme (https for example) and a port number if applicable
- **POSTGRES_DB** - The preferred name of the created database
- **POSTGRES_USER** - The username for the database
- **POSTGRES_PASSWORD** - The password for the database

### Set up Single Sign On (SSO)

Note the following directories in the repository's root:

- websp: This is the directory for the MAP(Shibboleth + Apache) container.
- openldap: This directory contains a LDAP container with a number of test users.
- idp: This is the directory for the IdP container.

#### Root Environment File

Follow the "env_example" file in the project root to create a local ".env" file in the project root directory.  Set up the host name and port for MAP1.
```bash
MAP1_HOST_NAME=map1.example.com
MAP1_HOST_PORT=8443
```

If evaluation or development requires multiple database nodes running simultaneously, to simulate interconnection & polling, configure additional nodes by incrementing the number after MAP, suc as "MAP2", "MAP3", etc.:
```bash
MAP2_HOST_NAME=map2.example.com
MAP2_HOST_PORT=9002
...
```

Ensure all host names provided above are also included in the "DJANGO_ALLOWED_HOSTS" item in the relevant file under the 'env' directory, for example, 'env/.env.dev', like:
```bash
DJANGO_ALLOWED_HOSTS=localhost app 127.0.0.1 [::1] websp websp1 websp2 host.docker.internal map1.example.com map2.example.com
```

#### Configure LDAP

Set up the admin password for LDAP in ".env" file, like:
```bash
LDAPPWD=ChangePassword
```

#### Configure the IdP Service

Set up a host name for the IdP in ".env" file, like
```bash
IDP_HOST_NAME=idp.example.org
```
To use the Embedded Discovery Service(EDS) for development or production, add/uncomment the following line in the root ".env" file.
```bash
IDP_SSO='<SSO discoveryProtocol="SAMLDS" discoveryURL="https://__MAP_HOST_NAME__:__MAP_HOST_PORT__/shibboleth-ds/index.html">SAML2 SAML1</SSO>'
```

#### Add Host Names For Local Routing

Add the MAPs' and IdP's host names to your computer's "/etc/hosts", like:
```bash
127.0.0.1   map1.example.com map2.example.com idp.example.org
```

#### Run SSO Configuration Script

From the project root directory, run the following script to generate all the needed configuration files for one IdP and one GREN Map DB Node:
```bash
./config_sso.sh
```
Or run with "-m <number>" option to generate the configuration files for one IdP and <number> GREN Map DB Nodes, as follows:
```bash
./config_sso.sh -m 2
```

### User Configuration

A Django user is automatically created every time a new user logs in through Shibboleth. The user's EPPN will be used as the Django username. Email, first name, and last name will be auto-filled if possible.  (They will not overwrite existing values if the user is created ahead of a Shibbolet login.)

At least one admin user should be pre-configured if possible.  Add known desired admin users' EPPNs, space-delimited, to environment files under "env/" folder (for example, "env/.env.prod", "env/.env.dev" ...)

```bash
ADMIN_EPPNS=testuser1@example.org testuser2@example.org
```

Once the application has started, an admin user can add more admin users to a DB Node by assigning both "Staff" and "Superuser" permissions to existing Django users, or new users can be pre-created with their EPPNs as their usernames.

### Build and Run the Application Containers

Run two commands to start the DB Node and IdP separately:
```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build
docker-compose -f docker-compose.idp.yml up -d --build
```
Or run in one command to start them together:
```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml -f docker-compose.idp.yml up --build
```

To start a second DB Node, if applicable:
```bash
docker-compose -f docker-compose.yml -f docker-compose.dev2.yml -p gren2 up -d
```

The container build process might take several minutes to build.  Run `docker ps` to check the containers' statuses.  Wait for all the containers become "healthy" (not "health: starting"), then open a browser (private window suggested) to access the GREN Map DB Node.

#### Apple Silicon (ARM-based) Macs

Container build may be slow on Apple Silicon by default.  To decrease build times:
1. Set the DOCKER_DEFAULT_PLATFORM from linux/amd64 to linux/arm64 in /.env:
```bash
# Environment variable for docker build
#DOCKER_DEFAULT_PLATFORM=linux/amd64
DOCKER_DEFAULT_PLATFORM=linux/arm64
```
2. Check "Use Rosetta for x86/amd64 emulation" option in Docker Desktop Preferences

### Access the GREN Map DB Node(s)

URLs for the first DB Node server:
- If you have not changed any defaults: `https://map1.example.com:8443`
- If the values in .env file have been changed, use the following format: `https://${MAP1_HOST_NAME}:${MAP1_HOST_PORT}`

Access a second MAP server at:
`https://${MAP2_HOST_NAME}:${MAP2_HOST_PORT}` (for example: `https://map2.example.com:9002`)

### Insert Data

Inserting REN data into this database can be done manually or by importing a file in GRENML format.

The node also supports import of a Excel spreadsheet in a particular template, via GRENML in the background; see https://github.com/grenmap/GRENML/blob/main/docs/Sample%20Conversion%20Spreadsheet/GREN_data.v1_0.xlsx for this template.  A Python library for producing GRENML by script, suitable for increased data gathering automation, is available:
```sh
pip install grenml
```

Please see the user guide in the docs/user directory for more information on [importing data](docs/user/grenml_import.md).

## More Information

Please find additional [documentation](docs/index.md) for this application in the `docs` directory.

## License

This project is licenced under the Apache Licence,  Version 2.0.
Please refer to [LICENSE.md](LICENSE.md) for details on the project license.

## Contributing

Please visit the [GitHub project page](https://github.com/grenmap/GREN-Map-DB-Node) and contact the administrators or developers for contribution guidance, and read [CONTRIBUTING.md](CONTRIBUTING.md) for details on the process for submitting pull requests.

## Code of conduct

Please read [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) for details on the code of conduct.
