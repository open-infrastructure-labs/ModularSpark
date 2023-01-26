#!/bin/bash
set -e
pushd "$(dirname "$0")"
ROOT=$(pwd)
source setup.sh

if [ ! -d $SERVER_DIR/storage ]; then
  echo "Initializing Server"
  sudo $SERVER_DIR/sbin/pvfs2-server -f $SERVER_DIR/etc/orangefs-server.conf
fi

sudo $SERVER_DIR/sbin/pvfs2-server $SERVER_DIR/etc/orangefs-server.conf