#!/bin/bash

SCRIPT_DIR="$(dirname $(realpath "$0"))"
echo $SCRIPT_DIR
pushd $SCRIPT_DIR
./mount.sh $SCRIPT_DIR/ramdisk
