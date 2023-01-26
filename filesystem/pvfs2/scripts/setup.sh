#!/bin/bash

WORKING_DIR=$(pwd)
ROOT_DIR=$(git rev-parse --show-toplevel)
echo "ROOT_DIR $ROOT_DIR"
echo "WORKING_DIR $WORKING_DIR"

source $ROOT_DIR/version
BUILD_DIR=$ROOT_DIR/filesystem/pvfs2/build
SERVER_DIR=$ROOT_DIR/filesystem/pvfs2/build/install_server
FUSE_DIR=$ROOT_DIR/filesystem/pvfs2/build/install_fuse

