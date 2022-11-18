#!/bin/bash
set -e # exit on error
ROOT_DIR=$(git rev-parse --show-toplevel)
source $ROOT_DIR/version

DOCKER_NAME=$(docker container ls -q --filter name="${BASE_SPARK_CONTAINER_NAME}-dc1")

if [ ! -z "$DOCKER_NAME" ]
then
  docker container stop ${DOCKER_NAME}
fi