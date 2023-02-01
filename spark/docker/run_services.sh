#!/bin/bash

set -e # exit on error

rm -f /opt/volume/status/WORKER_STATE

# Start ssh service
sudo service ssh start

pushd /R23/filesystem/pvfs2/orangefs_fuse
# check if pvfs2tab is present
if [ -f ./pvfs2tab ] 
then
    echo "Mounting orangefs_fuse"
    sudo mkdir -p /mnt/orangefs_fuse
    sudo chown ${USER}:${USER} /mnt/orangefs_fuse
    ./bin/pvfs2fuse /mnt/orangefs_fuse
    df -h /mnt/orangefs_fuse
else
    echo "Missing /R23/filesystem/pvfs2/orangefs_fuse/pvfs2tab"
fi
popd

echo "WORKER_READY"
echo "WORKER_READY" > /opt/volume/status/WORKER_STATE

echo "RUNNING_MODE $RUNNING_MODE"

if [ "$RUNNING_MODE" = "daemon" ]; then
    sleep infinity
fi

if mount | grep /mnt/orangefs_fuse; then 
    echo "Unmounting orangefs_fuse"
    fusermount -u /mnt/orangefs_fuse
fi

