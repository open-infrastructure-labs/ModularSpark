To mount fuse in debug mode:

pushd filesystem/adapter/pass_thru
mkdir fuse_data
chmod a+rwx fuse_data
mkdir fuse_mount
chmod a+rwx fuse_mount
# In the below we use -d for debug mode with fuse tracing
# -f runs the fuse application in the foreground.
# the "fuse_data" directory is the backing store for the fuse filesystem.
# the "fuse_mount" directory is where the fuse filesystem is mounted.
./fuse_pass_thru --path=/R23/R23/filesystem/adapter/pass_thru/fuse_data/ -o allow_other -d -f /R23/R23/filesystem/adapter/pass_thru/fuse_mount

# Inside docker:
cd /R23/filesystem/adapter/pass_thru
# ./fuse_pass_thru --path=/R23/filesystem/adapter/pass_thru/fuse_data/ -d -f /R23/filesystem/adapter/pass_thru/fuse_mount
./fuse_pass_thru --path=/R23/filesystem/adapter/pass_thru/fuse_data/  /R23/filesystem/adapter/pass_thru/fuse_mount

mount | grep fuse_pass_thru


# Run I/o
fio --randrepeat=1 --time_based=1 --do_verify=1 --verify=crc32c --verify_fatal=1 --runtime=30s --ioengine=libaio \
    --direct=1 --gtod_reduce=1 --name=test --bs=8k --io_size=8k --size=1M --iodepth=1 \
    --readwrite=write --filename=/R23/R23/filesystem/adapter/pass_thru/fuse_mount/test.fio

# To unmount:
fusermount -u /R23/R23/filesystem/adapter/pass_thru/fuse_mount


# Intersting links:
# https://github.com/s3fs-fuse/s3fs-fuse
