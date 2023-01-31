#!/bin/bash

# Verify example
#fio --randrepeat=1 --time_based=1 --do_verify=1 --verify=crc32c --verify_fatal=1 --runtime=30s --ioengine=libaio \
#    --direct=1 --gtod_reduce=1 --name=test --bs=8k --io_size=8k --size=100M --iodepth=1 \
#    --readwrite=write --filename=./fuse_mount/test.fio

# Runtime is determined by either time or I/O size. (Time takes precidence)
RUNTIME="--time_based=1 --runtime=10s"
echo "RUNTIME IS: $RUNTIME"
#RUNTIME=--io_size=10g

ONE_THREAD_FILE="--randrepeat=1 --ioengine=libaio --direct=0 --gtod_reduce=1 --name=test --filename=fuse_mount/test.fio"
one_thread_fio () { 
    CMD="fio $RUNTIME --bs=$1 --readwrite=$2 --size=$3 $ONE_THREAD_FILE"
    echo "**********************"
    echo "*  $CMD"
    echo "**********************"
    $CMD
}
SCALING_FILE="--randrepeat=1 --ioengine=libaio --direct=0 --gtod_reduce=1 --name=test --directory=fuse_mount --io_submit_mode=offload"
scaling_fio () { 
    CMD="fio $RUNTIME --bs=$1 --readwrite=$2 --iodepth=$3 --nrfiles=$3 --size=$4 $SCALING_FILE"
    echo "**********************"
    echo "*  $CMD"
    echo "**********************"
    $CMD
}

# 1 thread sequential read
one_thread_fio "8k" "read" "10m"
# 1 thread sequential write
one_thread_fio "8k" "read" "10m"

# 8k Scaling test sequential reads
scaling_fio "8k" "read" "1" "2g"
scaling_fio "8k" "read" "2" "2g"
scaling_fio "8k" "read" "4" "2g"
scaling_fio "8k" "read" "8" "2g"
scaling_fio "8k" "read" "16" "2g"
scaling_fio "8k" "read" "32" "2g"
scaling_fio "8k" "read" "64" "2g"

# 8k Scaling test sequential writes
scaling_fio "8k" "write" "1" "2g"
scaling_fio "8k" "write" "2" "2g"
scaling_fio "8k" "write" "4" "2g"
scaling_fio "8k" "write" "8" "2g"
scaling_fio "8k" "write" "16" "2g"
scaling_fio "8k" "write" "32" "2g"
scaling_fio "8k" "write" "64" "2g"

# 128k Scaling test sequential reads
scaling_fio "128k" "read" "1" "2g"
scaling_fio "128k" "read" "2" "2g"
scaling_fio "128k" "read" "4" "2g"
scaling_fio "128k" "read" "8" "2g"
scaling_fio "128k" "read" "16" "2g"
scaling_fio "128k" "read" "32" "2g"
scaling_fio "128k" "read" "64" "2g"

# 128k Scaling test sequential writes
scaling_fio "128k" "write" "1" "2g"
scaling_fio "128k" "write" "2" "2g"
scaling_fio "128k" "write" "4" "2g"
scaling_fio "128k" "write" "8" "2g"
scaling_fio "128k" "write" "16" "2g"
scaling_fio "128k" "write" "32" "2g"
scaling_fio "128k" "write" "64" "2g"