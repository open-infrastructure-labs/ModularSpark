#!/usr/bin/env bash

set -e # exit on error
pushd "$(dirname "$0")"
ROOT_DIR=$(git rev-parse --show-toplevel)
source $ROOT_DIR/version

# Set up docker networks to simulate dc to dc interconnect
# Check if qflock network exists
if ! docker network ls | grep ${BASE_NETWORK_NAME}; then
  docker network create ${BASE_NETWORK_NAME}
fi
