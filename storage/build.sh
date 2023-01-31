#!/usr/bin/env bash

set -e # exit on error
ROOT_DIR=$(git rev-parse --show-toplevel)
source $ROOT_DIR/version

STORAGE_DIR=${ROOT_DIR}/storage

# run storage docker with build command
${STORAGE_DIR}/start_storage_node.sh --cmd /R23/filesystem/pvfs2/build.sh
