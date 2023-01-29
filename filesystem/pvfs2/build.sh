#!/usr/bin/env bash

set -e # exit on error
pushd "$(dirname "$0")" # connect to root
ROOT_DIR=$(pwd)

SERVER_DIR=$ROOT_DIR/orangefs_server
FUSE_DIR=$ROOT_DIR/orangefs_fuse

echo "Start building PVFS2 ..."
mkdir -p ${SERVER_DIR}
mkdir -p ${FUSE_DIR}

pushd orangefs
# ./prepare command will generate ./configure script
./prepare

./configure --prefix=$SERVER_DIR --with-db-backend=lmdb

# On a systems with large core count we may run our of memory
make -j$((`nproc`/2))

mkdir -p $SERVER_DIR
# sudo chown $USER:$USER $SERVER_DIR
make install

# Building orangefs_fuse
# need libfuse-dev
./configure --prefix=$FUSE_DIR --disable-server --disable-usrint --disable-opt --enable-fuse --with-db-backend=lmdb

make -j$((`nproc`/2))

make install