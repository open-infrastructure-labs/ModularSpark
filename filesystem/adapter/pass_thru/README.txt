To bring up the fuse in debug mode:

# In the below we use -d for debug mode with fuse tracing
# -f runs the fuse application in the foreground.
# the "fuse_data" directory is the backing store for the fuse filesystem.
# the "fuse_mount" directory is where the fuse filesystem is mounted.
./fuse_pass_thru --path=/R23/R23/filesystem/fuse_data/ -o allow_other -d -f /R23/R23/filesystem/fuse_mount