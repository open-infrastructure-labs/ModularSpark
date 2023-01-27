#!/bin/bash

SCRIPT_DIR="$(dirname "$0")"
pushd $SCRIPT_DIR

if [ "$#" -lt 1 ]; then
  DATA_DIR="$SCRIPT_DIR/fuse_data"
else
  DATA_DIR="$1"
fi

if [ "$#" -lt 2 ]; then
  MOUNT_DIR="$SCRIPT_DIR/fuse_mount"
else
  MOUNT_DIR="$1"
fi


if [ ! -d $DATA_DIR ]; then
  mkdir $DATA_DIR
  chmod a+rwx $DATA_DIR
fi
if [ ! -d $MOUNT_DIR ]; then
  mkdir $MOUNT_DIR
  chmod a+rwx $MOUNT_DIR
fi
echo "DATA_DIR: $DATA_DIR"
echo "MOUNT_DIR: $MOUNT_DIR"

# In the below we use -d for debug mode with fuse tracing
# -f runs the fuse application in the foreground.
# the "fuse_data" directory is the backing store for the fuse filesystem.
# the "fuse_mount" directory is where the fuse filesystem is mounted.
#DEBUG_ARGS = "-d -f"
DEBUG_ARGS=""
#$SCRIPT_DIR/fuse_pass_thru --path=$DATA_DIR -o allow_other $DEBUG_ARGS $MOUNT_DIR
$SCRIPT_DIR/fuse_pass_thru --path=$DATA_DIR --log_path=$SCRIPT_DIR/logs -o allow_other $DEBUG_ARGS $MOUNT_DIR
