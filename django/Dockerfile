###########
# BUILDER #
###########

# pull official base image
FROM python:3.9-alpine as builder

# set work directory
WORKDIR /usr/src/app

# install the dependencies
RUN apk update; \
    apk add --no-cache less openssh postgresql-dev gcc python3-dev musl-dev git npm libxml2-dev libxslt-dev

# Copy source code
COPY . /usr/src/app/

# install dependencies
COPY ./requirements.txt .
RUN pip install --upgrade pip
RUN pip wheel --no-cache-dir --wheel-dir /usr/src/app/wheels -r requirements.txt

# Get the map visualization files and other browser files
RUN npm cache clean --force; \
    npm install

##############
# DEPLOYMENT #
##############

# Create the deployable container, this will be targeted as 'deployment' in the docker compose files
# For production deployment, we can build the specific layer we want:
#     https://docs.docker.com/develop/develop-images/multistage-build/#stop-at-a-specific-build-stage
#
#     docker build --target deployment -t django_deploy .

# pull official base image
FROM python:3.9-alpine as deployment

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV HOME=/home/grenmapadmin
ENV APP_HOME=/home/grenmapadmin/web

RUN apk -U upgrade; \
    apk add --no-cache bash; \
    apk add libpq gettext-dev dos2unix inotify-tools curl libxml2 libxslt; \
    addgroup -S grenmapadmin; \
    adduser -S grenmapadmin -u 1001 -G grenmapadmin; \
    mkdir -p $HOME/static/gren-map-visualization $APP_HOME/staticfiles $APP_HOME/media

WORKDIR $APP_HOME

# Install dependencies
COPY --from=builder /usr/src/app/wheels /wheels
COPY --from=builder /usr/src/app/requirements.txt .
RUN pip install --no-cache --upgrade pip; \
    pip install --no-cache /wheels/*; \
    pip install --upgrade setuptools

# Copy map visualization files
COPY --from=builder /usr/src/app/node_modules/\@grenmap/gren-map-visualization $HOME/static/gren-map-visualization

# copy project
COPY . $APP_HOME

# chown all the files to the app user
RUN chown -R grenmapadmin:grenmapadmin $HOME

# required to generate .mo files for django_q
RUN chown -R grenmapadmin:grenmapadmin $(find /usr/local/lib -name django_q)/locale

# change to the app user
USER grenmapadmin

# Converts windows style line endings to unix style if the host is windows
RUN dos2unix /home/grenmapadmin/web/entrypoint.sh; \
    dos2unix /home/grenmapadmin/web/collect_static.sh

ARG BUILD_TIMESTAMP
ARG GIT_COMMIT
ARG GIT_TAG
ARG AUTHORS

# Write build attributes as metadata in the image
LABEL org.opencontainers.image.authors=$AUTHORS
LABEL org.opencontainers.image.created=$BUILD_TIMESTAMP
LABEL org.opencontainers.image.revision=$GIT_COMMIT
LABEL org.opencontainers.image.version=$GIT_TAG
LABEL org.opencontainers.image.description="GREN Map Database Node - django image"

# Write a file containing the build attributes.
# Django will read it to populate the home admin page.
RUN SECRET_KEY=None python manage.py buildinfo ${GIT_COMMIT:-""} ${GIT_TAG:-""}

# run entrypoint.sh
ENTRYPOINT ["/home/grenmapadmin/web/entrypoint.sh"]

###############
# DEVELOPMENT #
###############

# Create a version of the deployable container with optimisations for local development.
# This will be targeted as 'development' in the docker compose files

FROM deployment as development

USER root

RUN apk add npm --no-cache
RUN npm install -g nodemon

# change to the app user
USER grenmapadmin

ENV PATH="/home/grenmapadmin/.local/bin:$PATH"
RUN pip install -r requirements.dev.txt

COPY run_tests_with_sqlite.sh /home/grenmapadmin/web

ENTRYPOINT ["/home/grenmapadmin/web/entrypoint.sh"]
