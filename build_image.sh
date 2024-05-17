#!/bin/bash

# get the organization name
ORGANIZATION_NAME=$1
if [ -z "$ORGANIZATION_NAME" ] ; then
    echo "Usage: build_image.sh ORGANIZATION_NAME"
    exit 1
fi

# check if trivy is available
if ! command -v trivy >/dev/null ; then
    echo "Please install trivy:"
    echo "https://aquasecurity.github.io/trivy/latest/getting-started/installation/"
    exit 1
fi

readonly APP_IMAGE_NAME="grenmap-django"
readonly WEBSP_IMAGE_NAME="grenmap-websp"
LABEL_TIMESTAMP=$(date -u "+%Y-%m-%dT%H:%M:%SZ")
TAG_TIMESTAMP=$(date -u "+%Y%m%dT%H%M%SZ")
GIT_COMMIT_SHA=$(git rev-parse HEAD)

# The output of "git describe" is the tag closest to HEAD,
# followed by the number of commits from HEAD to the tag,
# followed by "-g" plus the abbreviated SHA of the HEAD commit.
#
# 1.0.0-rc11-22-g069957d
# tag: 1.0.0-rc11
# number of commits between tag and HEAD: 22
# abbreviated SHA: 069957d
GIT_TAG=$(git describe --tags || echo "initial")

# build the image
docker buildx build \
    --build-arg BUILD_TIMESTAMP="$LABEL_TIMESTAMP" \
    --build-arg GIT_COMMIT="$GIT_COMMIT_SHA" \
    --build-arg GIT_TAG="$GIT_TAG" \
    --build-arg AUTHORS="$ORGANIZATION_NAME" \
    -f django/Dockerfile \
    -t "$APP_IMAGE_NAME" \
    --target deployment \
    --platform "linux/amd64,linux/arm64" \
    --output="type=image,name=${APP_IMAGE_NAME}:latest" \
    django
readonly DOCKER_BUILD_STATUS=$?
if [ "$DOCKER_BUILD_STATUS" -gt "0" ] ; then
    echo "Image build failed"
    exit 1
fi

# apply a tag on the app image
readonly APP_IMAGE_TAG="$GIT_TAG-$TAG_TIMESTAMP"
readonly APP_IMAGE_NAME_WITH_TAG="$APP_IMAGE_NAME:$APP_IMAGE_TAG"
docker tag "$APP_IMAGE_NAME" "$APP_IMAGE_NAME_WITH_TAG"

# build the websp image
docker buildx build \
    -f websp/Dockerfile \
    -t "$WEBSP_IMAGE_NAME" \
    --platform "linux/amd64,linux/arm64" \
    --output="type=image,name=${WEBSP_IMAGE_NAME}:latest" \
    websp

# apply a tag on the websp image
readonly WEBSP_IMAGE_TAG="$GIT_TAG-$TAG_TIMESTAMP"
readonly WEBSP_IMAGE_NAME_WITH_TAG="$WEBSP_IMAGE_NAME:$WEBSP_IMAGE_TAG"
docker tag "$WEBSP_IMAGE_NAME" "$WEBSP_IMAGE_NAME_WITH_TAG"

# scan with trivy
echo "scanning $APP_IMAGE_NAME for vulnerabilities with trivy..."
trivy -q image --exit-code 1 --severity HIGH,CRITICAL "$APP_IMAGE_NAME_WITH_TAG"

echo "scanning $WEBSP_IMAGE_NAME for vulnerabilities with trivy..."
trivy -q image --exit-code 1 --severity HIGH,CRITICAL "$WEBSP_IMAGE_NAME_WITH_TAG"

echo "Images built:"
echo "$APP_IMAGE_NAME_WITH_TAG"
echo "$WEBSP_IMAGE_NAME_WITH_TAG"
