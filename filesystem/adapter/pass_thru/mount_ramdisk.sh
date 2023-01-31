#!/bin/bash

SCRIPT_DIR="$(dirname "$0")"
pushd $SCRIPT_DIR

if [ "$#" -lt 1 ]; then
  RAMDISK_DIR="$SCRIPT_DIR/ramdisk"
else
  RAMDISK_DIR="$1"
fi
if [ ! -d $RAMDISK_DIR ]; then
  mkdir $RAMDISK_DIR
  chmod a+rwx $RAMDISK_DIR
fi
echo "RAMDISK_DIR: $RAMDISK_DIR"
sudo mount -t tmpfs -o size=2g fuse_ramdisk $RAMDISK_DIR