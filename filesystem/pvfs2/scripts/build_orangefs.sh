#!/bin/bash
set -e
pushd "$(dirname "$0")"
ROOT=$(pwd)
source setup.sh
if [ ! -d $BUILD_DIR ]; then
    mkdir -p $BUILD_DIR
fi
ORANGEFS_TAR_PATH=$BUILD_DIR/orangefs-2.9.8.tar.gz
ORANGEFS_DL_PATH=https://s3.amazonaws.com/download.orangefs.org/current/source/orangefs-2.9.8.tar.gz
ORANGEFS_PATH=$BUILD_DIR/orangefs-v.2.9.8
echo "ORANGEFS_PATH: $ORANGEFS_PATH"
if [ ! -f $ORANGEFS_TAR_PATH ]; then
  wget $ORANGEFS_DL_PATH -O $ORANGEFS_TAR_PATH
fi
if [ ! -f $ORANGEFS_TAR_PATH ]; then
  echo "does not exist! $ORANGEFS_TAR_PATH" #wget $ORANGEFS_DL_PATH
fi

if [ ! -d $ORANGEFS_PATH ]; then
    tar -xzf $ORANGEFS_TAR_PATH --directory $BUILD_DIR
fi
pushd $ORANGEFS_PATH
./configure --prefix=$SERVER_DIR --with-db-backend=lmdb

make -j 8

sudo mkdir $SERVER_DIR
sudo chown $USER:$USER $SERVER_DIR
make install

# Generate the configuration file for the server.
$SERVER_DIR/bin/pvfs2-genconfig -q --protocol tcp --ioservers r23-1-storage-dc1 --metaservers r23-1-storage-dc1 $SERVER_DIR/etc/orangefs-server.conf

