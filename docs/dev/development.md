# Development Guide Lines

## Package Installation

When adding a package to the project, certain steps have to be taken depending on the purpose of the package

### Production Packages

For packages that are needed for the operation of the project, the package needs to be listed in different locations depending on the purpose of installing it.

#### For Compiling Another Package

Packages that are needed to compile another package are to go in the builder container in the Dockerfile,

#### System Packages for Running the Project

Any packages that are needed for continued operation of the project are to be listed in the final container in the Dockerfile.

#### Python packages

Any python packages that are to be installed for the production version of the project must be listed, with their version number, in the requirements.pip file

### Development Only Packages

For packages that are for development only purposes, select steps need to be taken for importing those packages.

#### OS/System Packages

To install a development only package into the OS, modify the `Dockerfile` file with the respective RUN command in the "DEVELOPMENT" section.

#### Python Packages

To install a development only python package, modify the file `requirements.dev.pip` with the python package and version required.

## Local version replacement

For a couple of the libraries used in the project it may be useful to use a local version directly instead of having to publish the code before testing

### GRENML package

To replace the grenml package with a local version instead, mount a local version as a volume by creating and including an additional docker compose file with a volume mounting the folder on the host machine to the correct folder in the container.

The compose file should have a section for the app container, and an override for the volume
```yml
version: '3.7'

services:
  app:
    volumes:
      - <PATH_TO_FOLDER_ON_HOST>:/home/grenmapadmin/web/grenml
```

This works by allowing python to look in the source directory of the project for packages prior to looking in the installed dependencies. Any package can be overridden with this same logic.

- NOTE: The folder on the host should be the folder containing the "__init__.py" file, not its parent folder.

### Import excel package

To replace the package with a local version, follow the same steps as above, but replace the path in the volumes with the appropriate folder.

```yml
version: '3.7'

services:
  app:
    volumes:
      - <PATH_TO_FOLDER_ON_HOST>:/home/grenmapadmin/web/import_excel
```

### GREN Map Visualization

To replace the package with a local version, follow the same steps as above, but replace the path in the volumes with the appropriate folder.

```yml
version: '3.7'

services:
 websp:
    volumes:
      - <PATH_TO_DIST_FOLDER_ON_HOST>:/home/grenmapadmin/web/staticfiles/gren-map-visualization
```

Alternatively:
Change 'Devdepedency' in package.json to use local folder files replace it with `/usr/src/app/staticfiles/gren-map-visualization`. You can generate required files from visualiztion locally using `gren-map-visualization`. or use git commit id from gren-map-distribution repo to use specific version of files.

Example: `git+https://github.com/grenmap/gren-map-distribution.git#756d721b243e884c9a602ebd9edc03d2eb36daf4`

Copy the file(s) needed for the visualization (gren-map.js,styles.css) into the local 'django/staticfiles/gren-map-visualization' directory of the project after running a full compose up at least once. This should allow the file to be picked up live in development mode. This file will be overwritten on a full rebuild of the container structure, however it should be uncommon to perform a full build while in development.

### System Configuration

Follow the instruction in [SSO Document](SSO.md) to set up your environment for one IdP and one or more MAP nodes.
