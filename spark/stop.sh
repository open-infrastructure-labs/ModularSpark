#!/bin/bash
set -e # exit on error
ROOT_DIR=$(git rev-parse --show-toplevel)
source $ROOT_DIR/version

DOCKER_NAME=$(docker container ls -q --filter name="${BASE_SPARK_CONTAINER_NAME}-dc1")

if [ ! -z "$DOCKER_NAME" ]
then
  docker container stop ${DOCKER_NAME}
fi

WORKER_NAMES=$(docker container ls -q --filter name="${WORKER_CONTAINER_NAME}")

if [ ! -z "${WORKER_NAMES}" ]
then
  docker container stop ${WORKER_NAMES}
fi
