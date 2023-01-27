#!/bin/bash

# fio --randrepeat=1 --time_based=1 --do_verify=1 --verify=crc32c --verify_fatal=1 --runtime=30s --ioengine=libaio \
#     --direct=1 --gtod_reduce=1 --name=test --bs=4k --io_size=8k --size=1M --iodepth=1 \
#     --readwrite=write --filename=/fuse_mount/test.fio

TIME=5s
# fio --randrepeat=1 --time_based=1 --do_verify=0 --verify=crc32c --verify_fatal=1 --runtime=$TIME --ioengine=libaio \
#     --direct=0 --gtod_reduce=1 --name=test --bs=8k --io_size=8k --size=100M --iodepth=1 \
#     --readwrite=write --filename=ramdisk/test.fio
# fio --randrepeat=1 --time_based=1 --do_verify=0 --verify=crc32c --verify_fatal=1 --runtime=$TIME --ioengine=libaio \
#     --direct=0 --gtod_reduce=1 --name=test --bs=8k --io_size=8k --size=100M --iodepth=1 \
#     --readwrite=read --filename=ramdisk/test.fio
fio --randrepeat=1 --time_based=1 --do_verify=0 --verify=crc32c --verify_fatal=1 --runtime=$TIME --ioengine=libaio \
    --direct=0 --gtod_reduce=1 --name=test --bs=8k --io_size=8k --size=100M --iodepth=1 \
    --readwrite=write --filename=fuse_mount/test.fio
fio --randrepeat=1 --time_based=1 --do_verify=0 --verify=crc32c --verify_fatal=1 --runtime=$TIME --ioengine=libaio \
    --direct=0 --gtod_reduce=1 --name=test --bs=8k --io_size=8k --size=100M --iodepth=1 \
    --readwrite=read --filename=fuse_mount/test.fio
