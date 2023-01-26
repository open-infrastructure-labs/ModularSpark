#!/bin/bash
set -e
pushd "$(dirname "$0")"
ROOT=$(pwd)
source setup.sh

if [ ! -d $FUSE_DIR ]; then
  mkdir -p $FUSE_DIR 
fi

ORANGEFS_PATH=$BUILD_DIR/orangefs-v.2.9.8
pushd $ORANGEFS_PATH

# need libfuse-dev
./configure --prefix=$FUSE_DIR --disable-server --disable-usrint --disable-opt --enable-fuse --with-db-backend=lmdb
make -j 8
make install
