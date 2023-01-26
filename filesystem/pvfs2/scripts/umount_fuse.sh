#!/bin/bash
set -e
pushd "$(dirname "$0")"
ROOT=$(pwd)
source setup.sh

if [ ! -d $FUSE_DIR ]; then
  echo "please build orangefs fuse first."
  exit 1
fi
 
CLIENT_MOUNT_DIR=$BUILD_DIR/client_mount
fusermount -u $CLIENT_MOUNT_DIR

echo "pvfs2 unmounted from: $CLIENT_MOUNT_DIR"