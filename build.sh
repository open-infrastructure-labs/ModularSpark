#!/bin/bash
set -e
pushd "$(dirname "$0")" # connect to root
ROOT_DIR=$(git rev-parse --show-toplevel)

# Initialize network configuration
${ROOT_DIR}/scripts/init_networks.sh


pushd storage/docker
./build.sh
popd

spark/docker/build.sh

pushd spark
./build.sh
popd

pushd benchmark
./build.sh
popd

