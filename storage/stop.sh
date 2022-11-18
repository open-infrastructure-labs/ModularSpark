#!/usr/bin/env bash

set -e # exit on error
ROOT_DIR=$(git rev-parse --show-toplevel)
source $ROOT_DIR/version
STORAGE_DOCKER=$(docker container ls -q --filter name="${BASE_STORAGE_CONTAINER_NAME}*")

if [ ! -z "$STORAGE_DOCKER" ]
then
  docker container stop ${STORAGE_DOCKER}
fi