#!/usr/bin/env bash

set -e # exit on error
pushd "$(dirname "$0")"
ROOT_DIR=$(git rev-parse --show-toplevel)
source $ROOT_DIR/version

# Check if BASE_NETWORK_NAME network exists
if ! docker network ls | grep ${BASE_NETWORK_NAME}; then
  docker network create ${BASE_NETWORK_NAME}
fi

# Check if STORAGE_NETWORK network exists
if ! docker network ls | grep ${STORAGE_NETWORK}; then
  docker network create ${STORAGE_NETWORK}
fi