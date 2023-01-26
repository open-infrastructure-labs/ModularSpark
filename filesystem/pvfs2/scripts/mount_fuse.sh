#!/bin/bash
set -e
pushd "$(dirname "$0")"
ROOT=$(pwd)
source setup.sh

if [ ! -d $FUSE_DIR ]; then
  echo "please build pvfs2 fuse first."
  exit 1
fi
 
CLIENT_MOUNT_DIR=$BUILD_DIR/client_mount
if [ ! -d $CLIENT_MOUNT_DIR ]; then
  mkdir -p $CLIENT_MOUNT_DIR
  chmod a+rwx $CLIENT_MOUNT_DIR
fi
$FUSE_DIR/bin/pvfs2fuse $CLIENT_MOUNT_DIR -o fs_spec=tcp://172.22.0.2:3334/orangefs

echo "pvfs2 mounted at: $CLIENT_MOUNT_DIR"