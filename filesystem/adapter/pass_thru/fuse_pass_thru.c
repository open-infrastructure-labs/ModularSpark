/*****************************************************************************
 * Licensed to the Apache Software Foundation (ASF) under one or more
 * contributor license agreements.  See the NOTICE file distributed with
 * this work for additional information regarding copyright ownership.
 * The ASF licenses this file to You under the Apache License, Version 2.0
 * (the "License"); you may not use this file except in compliance with
 * the License.  You may obtain a copy of the License at
 *
 *    http: *www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *****************************************************************************/
 
 /* compile:
  *   gcc -Wall fuse_pass_thru.c `pkg-config fuse3 --cflags --libs` -o fuse_pass_thru
  *   gcc -Wall fuse_pass_thru.c -ggdb `pkg-config fuse3 --cflags --libs` -o fuse_pass_thru
  * 
  * run:
  *   ./fuse_pass_thru --path=test -d -f --path=/nvme-part/R23/R23/fuse/fuse_adapter/test mount_point
  */

#define FUSE_USE_VERSION 31

#include <fuse3/fuse.h>
#include <stdio.h>
#include <string.h>
#include <errno.h>
#include <fcntl.h>
#include <stddef.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <sys/xattr.h>
#include <dirent.h>
#include <malloc.h>

#include "../../logging/src/lib/logger.h"

#ifdef DISABLE_LOGGER
void logger_init(const char *log_path){}
void logger_record_generic(log_opcode_t op,
                           const char *filename,
                           uint64_t handle,
                           unsigned long arg0, unsigned long arg1, unsigned long arg2, unsigned long arg3){}

void logger_record_open(const char *filename,
                        uint32_t flags,
                        uint64_t handle){}

void logger_record_rw(log_opcode_t op,
                      uint64_t handle,
                      const char *filename,
                      uint64_t offset,
                      uint64_t length){}

#endif

typedef struct fuse_adapter_options_s {
  int loopback; /* 0-no effect, 1-loopback enabled. */
  const char *path; /* Path to our remote. */
  const char *log_path; /* Path to logs. */
  int help; /* Set if help display is requested. */  
} fuse_adapter_options_t;

static fuse_adapter_options_t fuse_adapter_options;

typedef struct fuse_opt fuse_opt_t;

static fuse_opt_t fuse_adapter_options_spec[] = {
  {"--loopback", offsetof(fuse_adapter_options_t, loopback), 1 },
  {"--path=%s", offsetof(fuse_adapter_options_t, path), 1 },
  {"--log_path=%s", offsetof(fuse_adapter_options_t, log_path), 1 },
  {"--help", offsetof(fuse_adapter_options_t, help), 1 },
};

static char * alloc_new_path(const char *path)
{
    /* Below add one since strlen does not include null terminator.*/
    unsigned int new_path_len = strlen(path) + strlen(fuse_adapter_options.path) + 1;
    char *new_path = (char*) malloc(new_path_len);
    strcpy(new_path, fuse_adapter_options.path);
    strcat(new_path, path);
    return new_path;
}


static int fuse_adapter_getattr(const char *path, struct stat *stbuf,
			                    struct fuse_file_info *fi)
{
	(void) fi;
	int res = 0;

	memset(stbuf, 0, sizeof(struct stat));

    struct stat attr;
    char *new_path = alloc_new_path(path);

    if (stat(new_path, &attr) < 0) {
        printf("getattr: %s error: %d\n", new_path, -errno);
        res = -errno;
    } else {
        // printf("getattr: %s\n", str);
        stbuf->st_atime = attr.st_atime;
        stbuf->st_blksize = attr.st_blksize;
        stbuf->st_blocks = attr.st_blocks;
        stbuf->st_ctime = attr.st_ctime;
        stbuf->st_dev = attr.st_dev;
        stbuf->st_gid = attr.st_gid;
        stbuf->st_mode = attr.st_mode;
        stbuf->st_mtime = attr.st_mtime;
		stbuf->st_nlink = attr.st_nlink;
        stbuf->st_rdev = attr.st_rdev;
		stbuf->st_size = attr.st_size;
        stbuf->st_uid = attr.st_uid;
    }
    free(new_path);
    logger_record_generic(LOG_OPCODE_GETATTR, path, 
                          (fi != NULL) ? fi->fh : LOG_HANDLE_INVALID,
                          0, 0, 0, 0);
	return res;
}

static int fuse_adapter_readlink(const char *path, char *buffer, size_t size)
{
    char *new_path = alloc_new_path(path);
	int err;
    logger_record_generic(LOG_OPCODE_READLINK, path,  
                          LOG_HANDLE_INVALID,
                          0, 0, 0, 0);

	err = readlink(new_path, buffer, size - 1);
    free(new_path);
    if (err == -1) {
        err = -errno;
        return err;
    }

	buffer[err] = '\0';
	return 0;
}


static int fuse_adapter_mknod(const char *path, mode_t mode, dev_t dev)
{
    char *new_path = alloc_new_path(path);
	int err;
    logger_record_generic(LOG_OPCODE_MKNOD, path, 
                          LOG_HANDLE_INVALID,
                          mode, dev, 0, 0);
    
    err = mknod(new_path, mode, dev);
    free(new_path);
    if (err == -1) {
        // error returned, change error returned to -errno errno
        return -errno;
    }
	return 0;
}

static int fuse_adapter_mkdir(const char *path, mode_t mode)
{
    char *new_path = alloc_new_path(path);
    int err;
    logger_record_generic(LOG_OPCODE_MKDIR, path, 
                          LOG_HANDLE_INVALID,
                          mode, 0, 0, 0);
    // mode |= 0700; /* Make sure user has execute permission.*/

    err = mkdir(new_path, mode);
    free(new_path);
    if (err == -1) {
        // error returned, change error returned to -errno errno
        return -errno;
    }
	return 0;
}

static int fuse_adapter_unlink(const char *path)
{
    char *new_path = alloc_new_path(path);
    logger_record_generic(LOG_OPCODE_UNLINK, path, 
                          LOG_HANDLE_INVALID,
                          0, 0, 0, 0);

    if (unlink(new_path) == -1) {
        // error returned, change error returned to -errno errno
        free(new_path);
        return -errno;
    }
    free(new_path);
	return 0;
}

static int fuse_adapter_rmdir(const char *path)
{
    char *new_path = alloc_new_path(path);
    int err;
    logger_record_generic(LOG_OPCODE_RMDIR, path, 
                          LOG_HANDLE_INVALID,
                          0, 0, 0, 0);

    err = rmdir(new_path);
    free(new_path);
    if (err == -1) {
        // error returned, change error returned to -errno errno
        return -errno;
    }
	return 0;
}

static int fuse_adapter_symlink(const char *target, const char *linkpath)
{
    char *target_str = alloc_new_path(target);
    char *link_str = alloc_new_path(linkpath);
    int err;
    logger_record_generic(LOG_OPCODE_SYMLINK, target, 
                          LOG_HANDLE_INVALID,
                          0, 0, 0, 0);
    err = symlink(target_str, link_str);
    free(target_str);
    free(link_str);
    if (err == -1) {
        // error returned, change error returned to -errno errno
        return -errno;
    }
	return 0;
}

static int fuse_adapter_rename(const char *from, const char *to, unsigned int flags)
{
    char *from_path = alloc_new_path(from);
    char *to_path = alloc_new_path(to);
    int err;
    logger_record_generic(LOG_OPCODE_RENAME, from, 
                          LOG_HANDLE_INVALID,
                          0, 0, 0, 0);
    
	if (flags) {
        free(from_path);
        free(to_path);
		return -EINVAL;
    }
    err = rename(from_path, to_path);
    free(from_path);
    free(to_path);
	if (err == -1) {
		return -errno;
    }
	return 0;
}

static int fuse_adapter_link(const char *from, const char *to)
{
    char *from_path = alloc_new_path(from);
    char *to_path = alloc_new_path(to);
    int err;
    logger_record_generic(LOG_OPCODE_LINK, from, 
                          LOG_HANDLE_INVALID,
                          0, 0, 0, 0);
    
    err = link(from_path, to_path);
    free(from_path);
    free(to_path);
	if (err == -1) {
		return -errno;
    }
	return 0;
}

static int fuse_adapter_chmod(const char *path,
                              mode_t mode,
		                      struct fuse_file_info *fi)
{
    char *new_path = alloc_new_path(path);
    logger_record_generic(LOG_OPCODE_CHMOD, path, 
                          (fi != NULL) ? fi->fh : LOG_HANDLE_INVALID,
                          mode, 0, 0, 0);

    if (chmod(new_path, mode) == -1) {
        // error returned, change error returned to -errno errno
        free(new_path);
        return -errno;
    }
    free(new_path);
	return 0;
}

static int fuse_adapter_chown(const char *path,
                              uid_t uid, gid_t gid,
		                      struct fuse_file_info *fi)
{
    char *new_path = alloc_new_path(path);
    logger_record_generic(LOG_OPCODE_CHOWN, path, 
                          (fi != NULL) ? fi->fh : LOG_HANDLE_INVALID,
                          uid, gid, 0, 0);

    int err = lchown(new_path, uid, gid);
    
    if (err == -1) {
        printf("chown: %s, %d:%d error is: %d\n",
                new_path, uid, gid, -errno);
        free(new_path);
        // error returned, change error returned to -errno errno
        return -errno;
    }
    free(new_path);
	return 0;
}

static int fuse_adapter_truncate(const char *path,
                                 off_t size,
			                     struct fuse_file_info *fi)
{
    int err;
    char *new_path = NULL;
    logger_record_generic(LOG_OPCODE_CHOWN, path, 
                          (fi != NULL) ? fi->fh : LOG_HANDLE_INVALID,
                          size, 0, 0, 0);
    if (fi != NULL && fi->fh != 0) {
	    err = ftruncate(fi->fh, size);
    } else {
        new_path = alloc_new_path(path);
	    err = truncate(new_path, size);
    }
    if (new_path != NULL) {
        free(new_path);
    }
    if (err == -1) {
        // error returned, change error returned to -errno errno
        return -errno;
    }
	return 0;
}

static int fuse_adapter_open(const char *path, struct fuse_file_info *fi)
{
    char *new_path = alloc_new_path(path);

    int err = open(new_path, fi->flags);
    if (err == -1) {
        free(new_path);
        return -errno;
    }
    fi->fh = err;
    free(new_path);
    logger_record_open(path, fi->flags, fi->fh);
	return 0;
}

static int fuse_adapter_read(const char *path, char *buf, size_t size, off_t off,
		                     struct fuse_file_info *fi)
{
    logger_record_rw(LOG_OPCODE_READ, 0, path, off, size);
    if (fuse_adapter_options.loopback) {
        memset(buf, 0, size);
        return size;
    }
    int fd;
	size_t bytes;

    if (path != NULL) {
        char *new_path = alloc_new_path(path);
        fd = open(new_path, O_RDONLY);
        free(new_path);
    } else {
        fd = fi->fh;
    }
    if (fd < 0) {
        printf("%s: open error %d\n", __FUNCTION__, -errno);
        return -errno;
    }
    bytes = pread(fd, buf, size, off);

    if (bytes == -1) {
        bytes = -errno;
    }
    if (path != NULL) {
        close(fd);
    }
	return bytes;
}

static int fuse_adapter_write(const char *path, const char *buf, size_t size, off_t off,
		                      struct fuse_file_info *fi)
{   
    logger_record_rw(LOG_OPCODE_WRITE, 0, path, off, size);
    if (fuse_adapter_options.loopback) {
        return size;
    }
    int fd = 0;
	size_t bytes;
    if (path != NULL) {
        char *new_path = alloc_new_path(path);
        fd = open(new_path, O_WRONLY);
        free(new_path);
    } else {
        fd = fi->fh;
    }
    if (fd < 0) {
        printf("%s: open error %d\n", __FUNCTION__, -errno);
        return -errno;
    }
    bytes = pwrite(fd, buf, size, off);

    if (bytes == -1) {
        bytes = -errno;
    }
    if (path != NULL) {
        close(fd);
    }    
	return bytes;
}

static int fuse_adapter_statfs(const char *path, struct statvfs *stat)
{
    char *new_path = alloc_new_path(path);

    if (statvfs(new_path, stat) == -1) {
        // error returned, change error returned to -errno errno
        free(new_path);
        return -errno;
    }
    free(new_path);
    logger_record_generic(LOG_OPCODE_STATFS, path, 0, 0, 0, 0, 0);
	return 0;
}

static int fuse_adapter_flush(const char *path, struct fuse_file_info *fi)
{
    /* Nothing to do here. */
	(void) path;
	(void) fi;
    logger_record_generic(LOG_OPCODE_FLUSH, path, 
                          (fi != NULL) ? fi->fh : LOG_HANDLE_INVALID,
                          0, 0, 0, 0);
	return 0;
}

static int fuse_adapter_release(const char *path, struct fuse_file_info *fi)
{
    /* Nothing to do here. */
	(void) path;
	close(fi->fh);
    logger_record_generic(LOG_OPCODE_RELEASE, path, 
                          (fi != NULL) ? fi->fh : LOG_HANDLE_INVALID,
                          0, 0, 0, 0);
	return 0;
}

static int fuse_adapter_fsync(const char *path, int data,
		                      struct fuse_file_info *fi)
{
	/* Nothing to do here */
	(void) path;
	(void) data;
	(void) fi;
    logger_record_generic(LOG_OPCODE_FSYNC, path, 
                          (fi != NULL) ? fi->fh : LOG_HANDLE_INVALID,
                          0, 0, 0, 0);
	return 0;
}

void check_replace(const char *input, char **output)
{
    const char search[] = "trusted.";
    const char replace[] = "user.";
    int replace_len = strlen(replace);
    int search_len = strlen(search);
    if (strncmp(input, search, search_len) == 0) {
        int new_string_len = replace_len + strlen(input) - search_len + 1;
        char *new_string = (char*) malloc(new_string_len);
        strcpy(new_string, replace);
        strncpy(&new_string[replace_len],
                &input[search_len],
                new_string_len - replace_len);
        *output = new_string;
    } else {
        *output = NULL;
    }
}

static int fuse_adapter_setxattr(const char *path, const char *name,
                                 const char *value, long unsigned int size, int flags) 
{
    char *new_path = alloc_new_path(path);

    int err = lsetxattr(new_path, name, value, size, flags);
    logger_record_generic(LOG_OPCODE_SETXATTR, path, 
                          LOG_HANDLE_INVALID,
                          size, flags, 0, 0);
    free(new_path);
    if (err == -1) {
        printf("setxattr: path: %s name: %s err: %d\n", path, name, -errno);
        err = -errno;
    }
    return err;
}

static int fuse_adapter_getxattr(const char *path, const char *name,
                                 char *value, long unsigned int size) 
{
    char *new_path = alloc_new_path(path);
    logger_record_generic(LOG_OPCODE_GETXATTR, path, 
                          LOG_HANDLE_INVALID,
                          size, 0, 0, 0);
#if 1                        
    int err = lgetxattr(new_path, name, value, size);
    free(new_path);
    if (err == -1) {
        // printf("getxattr: path: %s name: %s err: %d\n", path, name, -errno);
        err = -errno;
    }
    return err;
#endif
    return 0;
}

static int fuse_adapter_listxattr(const char *path, char *list, size_t size) 
{
    char *new_path = alloc_new_path(path);
    logger_record_generic(LOG_OPCODE_LISTXATTR, path, 
                          LOG_HANDLE_INVALID,
                          size, 0, 0, 0);

    int err = llistxattr(new_path, list, size);
    free(new_path);
    if (err == -1) {
        printf("listxattr %s err: %d\n", new_path, errno);
        err = -errno;
    }
    return err;
}

static int fuse_adapter_removexattr(const char *path, const char *name) 
{
    char *new_path = alloc_new_path(path);
    char str[80];
    strcpy(str, fuse_adapter_options.path);
    strcat(str, path);
    logger_record_generic(LOG_OPCODE_REMOVEXATTR, path, 
                          LOG_HANDLE_INVALID,
                          0, 0, 0, 0);

    int err = lremovexattr(new_path, name);
    free(new_path);
    if (err == -1) {
        printf("removexxattr %s err: %d\n", new_path, errno);
        err = -errno;
    }
    return err;
}
static int fuse_adapter_readdir(const char *path, void *buf, fuse_fill_dir_t filler,
		                        off_t offset, struct fuse_file_info *fi,
		                        enum fuse_readdir_flags flags)
{
	(void) offset;
	(void) fi;
	(void) flags;

    char *new_path = alloc_new_path(path);

    DIR *ds = NULL;

	ds = opendir(new_path);
    free(new_path);
	if (ds == NULL) {
		return -errno;
    }
	
	struct dirent *dir_ent = NULL;
	struct stat st;
	memset(&st, 0, sizeof(st));
    
	while ((dir_ent = readdir(ds)) != NULL) {
		st.st_ino = dir_ent->d_ino;
        /* Convert from dirent to entries used with st.st_mode. 
         */
		st.st_mode = DTTOIF(dir_ent->d_type);
		if (filler(buf, dir_ent->d_name, &st, 0, 0)) {
			break;
        }
	}
	closedir(ds);
    logger_record_generic(LOG_OPCODE_READDIR, path, 
                          (fi != NULL) ? fi->fh : LOG_HANDLE_INVALID,
                          0, 0, 0, 0);
	return 0;
}

static int fuse_adapter_releasedir(const char *path, struct fuse_file_info *fi)
{
    (void) path;
    (void) fi;
    /* Nothing to do. */
    logger_record_generic(LOG_OPCODE_RELEASEDIR, path, 
                          (fi != NULL) ? fi->fh : LOG_HANDLE_INVALID,
                          0, 0, 0, 0);
    return 0;
}

static int fuse_adapter_fsyncdir(const char *path,
                                 int fsyncdir,
                                 struct fuse_file_info *fi)
{
    (void) path;
    (void) fi;
    /* Nothing to do. */
    logger_record_generic(LOG_OPCODE_FSYNCDIR, path, 
                          (fi != NULL) ? fi->fh : LOG_HANDLE_INVALID,
                          0, 0, 0, 0);
    return 0;
}
static void fuse_show_cap(struct fuse_conn_info *conn, unsigned int cap)
{	
	if (cap & FUSE_CAP_ASYNC_READ) {
	    printf("\tFUSE_CAP_ASYNC_READ\n");
    }
	if (cap & FUSE_CAP_POSIX_LOCKS) {
		printf("\tFUSE_CAP_POSIX_LOCKS\n");
    }
	if (cap & FUSE_CAP_ATOMIC_O_TRUNC) {
		printf("\tFUSE_CAP_ATOMIC_O_TRUNC\n");
    }
	if (cap & FUSE_CAP_EXPORT_SUPPORT) {
		printf("\tFUSE_CAP_EXPORT_SUPPORT\n");
    }
	if (cap & FUSE_CAP_DONT_MASK) {
		printf("\tFUSE_CAP_DONT_MASK\n");
    }
	if (cap & FUSE_CAP_SPLICE_WRITE) {
		printf("\tFUSE_CAP_SPLICE_WRITE\n");
    }
	if (cap & FUSE_CAP_SPLICE_MOVE) {
		printf("\tFUSE_CAP_SPLICE_MOVE\n");
    }
	if (cap & FUSE_CAP_SPLICE_READ) {
		printf("\tFUSE_CAP_SPLICE_READ\n");
    }
	if (cap & FUSE_CAP_SPLICE_WRITE) {
		printf("\tFUSE_CAP_SPLICE_WRITE\n");
    }
	if (cap & FUSE_CAP_FLOCK_LOCKS) {
		printf("\tFUSE_CAP_FLOCK_LOCKS\n");
    }
	if (cap & FUSE_CAP_IOCTL_DIR) {
		printf("\tFUSE_CAP_IOCTL_DIR\n");
    }
	if (cap & FUSE_CAP_AUTO_INVAL_DATA) {
		printf("\tFUSE_CAP_AUTO_INVAL_DATA\n");
    }
	if (cap & FUSE_CAP_READDIRPLUS) {
		printf("\tFUSE_CAP_READDIRPLUS\n");
    }
	if (cap & FUSE_CAP_READDIRPLUS_AUTO) {
		printf("\tFUSE_CAP_READDIRPLUS_AUTO\n");
    }
	if (cap & FUSE_CAP_ASYNC_DIO) {
		printf("\tFUSE_CAP_ASYNC_DIO\n");
    }
	if (cap & FUSE_CAP_WRITEBACK_CACHE) {
		printf("\tFUSE_CAP_WRITEBACK_CACHE\n");
    }
	if (cap & FUSE_CAP_NO_OPEN_SUPPORT) {
		printf("\tFUSE_CAP_NO_OPEN_SUPPORT\n");
    }
	if (cap & FUSE_CAP_PARALLEL_DIROPS) {
		printf("\tFUSE_CAP_PARALLEL_DIROPS\n");
    }
	if (cap & FUSE_CAP_POSIX_ACL) {
		printf("\tFUSE_CAP_POSIX_ACL\n");
    }
	if (cap & FUSE_CAP_HANDLE_KILLPRIV) {
		printf("\tFUSE_CAP_HANDLE_KILLPRIV\n");
    }
	if (cap & FUSE_CAP_NO_OPENDIR_SUPPORT) {
		printf("\tFUSE_CAP_NO_OPENDIR_SUPPORT\n");
    }
	if (cap & FUSE_CAP_EXPLICIT_INVAL_DATA) {
		printf("\tFUSE_CAP_EXPLICIT_INVAL_DATA\n");
    }
}
static void * fuse_adapter_init(struct fuse_conn_info *conn,
			                    struct fuse_config *cfg)
{
	(void) conn;
	(void) cfg;

    /* Only init logging if the --log_path provided. */
    if (strlen(fuse_adapter_options.log_path) != 0) {
        logger_init(fuse_adapter_options.log_path);
    }
    
	printf("Protocol version: %d.%d\n", conn->proto_major,
	       conn->proto_minor);
    printf("conn->max_read: 0x%x\n", conn->max_read);
    printf("conn->max_write: 0x%x\n", conn->max_write);
    printf("conn->max_readahead: 0x%x\n", conn->max_readahead);
    printf("conn->max_write: 0x%x\n", conn->max_write);

    printf("conn->capable: 0x%x\n", conn->capable);
    printf("fuse_conn_info->capable\n");
    fuse_show_cap(conn, conn->capable);

    printf("conn->want: 0x%x\n", conn->want);
    printf("fuse_conn_info->want\n");
    fuse_show_cap(conn, conn->want);

    printf("cfg->kernel_cache: 0x%x\n", cfg->kernel_cache);
    printf("cfg->direct_io: 0x%x\n", cfg->direct_io);
    printf("cfg->auto_cache: 0x%x\n", cfg->auto_cache);

    // conn->want &= ~FUSE_CAP_AUTO_INVAL_DATA;
    //conn->want |= FUSE_CAP_WRITEBACK_CACHE;
    cfg->direct_io = 1;
    printf("conn->want: 0x%x\n", conn->want);
    printf("Capabilities: new want\n");
    fuse_show_cap(conn, conn->want);
    // cfg->kernel_cache = 1;
    logger_record_generic(LOG_OPCODE_INIT, NULL, 
                          LOG_HANDLE_INVALID,
                          0, 0, 0, 0);
	return NULL;
}

static void fuse_adapter_destroy(void *private_data)
{
	(void) private_data;
    logger_record_generic(LOG_OPCODE_DESTROY, NULL, 
                          LOG_HANDLE_INVALID,
                          0, 0, 0, 0);
}

static int fuse_adapter_access(const char *path, int flags) 
{
    char *new_path = alloc_new_path(path);

    int err = access(new_path, flags);
    free(new_path);
    if (err == -1) {
        err = -errno;
    }
    return err;
}

static int fuse_adapter_create(const char *path,
                               mode_t mode,
		                       struct fuse_file_info *fi) 
{
    char *new_path = alloc_new_path(path);
    logger_record_generic(LOG_OPCODE_CREATE, path, 
                          (fi != NULL) ? fi->fh : LOG_HANDLE_INVALID,
                          mode, 0, 0, 0);

    int err = open(new_path, fi->flags, mode);
    free(new_path);
    if (err == -1) {
        err = -errno;
        return err;
    }
    fi->fh = err;
    return 0;
}

static int fuse_adapter_utimens(const char *path,
                                const struct timespec ts[2],
		                        struct fuse_file_info *fi)
{
	(void) fi;
    char *new_path = alloc_new_path(path);
	int err;
    logger_record_generic(LOG_OPCODE_UTIMENS, path, 
                          (fi != NULL) ? fi->fh : LOG_HANDLE_INVALID,
                          0, 0, 0, 0);
	
	err = utimensat(0, new_path, ts, AT_SYMLINK_NOFOLLOW);
    free(new_path);
	if (err == -1) {
        return -errno;
    }
	return 0;
}

static int fuse_adapter_fallocate(const char *path,
                                  int mode,
                                  off_t off,
                                  off_t len,
                                  struct fuse_file_info *fi) 
{
    int fd;
	size_t err;
    char *new_path = NULL;
    logger_record_rw(LOG_OPCODE_FALLOCATE,
                     (fi != NULL) ? fi->fh : LOG_HANDLE_INVALID,
                     path, off, len);

    if (path != NULL) {
        new_path = alloc_new_path(path);
        fd = open(new_path, O_WRONLY);
    } else {
        fd = fi->fh;
    }
    free(new_path);
    if (fd < 0) {
        printf("%s: open error %d\n", __FUNCTION__, -errno);
        return -errno;
    }
    err = posix_fallocate(fd, off, len);

    if (path != NULL) {
        close(fd);
    }
	return -err;
}

static off_t fuse_adapter_lseek(const char *path,
                                off_t off,
                                int from,
                                struct fuse_file_info *fi) 
{
    int fd;
	size_t err;
    char *new_path = NULL;
    logger_record_rw(LOG_OPCODE_LSEEK,
                     (fi != NULL) ? fi->fh : LOG_HANDLE_INVALID,
                     path, off, from);

    if (path != NULL) {
        new_path = alloc_new_path(path);
        fd = open(new_path, O_WRONLY);
    } else {
        fd = fi->fh;
    }
    free(new_path);
    if (fd < 0) {
        printf("%s: open error %d\n", __FUNCTION__, -errno);
        return -errno;
    }
    err = lseek(fd, off, from);

    if (path != NULL) {
        close(fd);
    }
	return err;
}


static const struct fuse_operations fuse_adapter_ops = {
	.getattr	 = fuse_adapter_getattr,
    .readlink    = fuse_adapter_readlink,

    .mknod       = fuse_adapter_mknod,
    .mkdir       = fuse_adapter_mkdir,
    .unlink      = fuse_adapter_unlink,
    .rmdir       = fuse_adapter_rmdir,

    .symlink     = fuse_adapter_symlink,
    .rename      = fuse_adapter_rename,
    .link        = fuse_adapter_link,

    .chmod      = fuse_adapter_chmod,
    .chown      = fuse_adapter_chown,
    .truncate   = fuse_adapter_truncate,

    .open		 = fuse_adapter_open,
	.read 		 = fuse_adapter_read,
	.write	 	 = fuse_adapter_write,
    .statfs      = fuse_adapter_statfs,
    
    .flush       = fuse_adapter_flush,
    .release     = fuse_adapter_release,
    .fsync       = fuse_adapter_fsync,

    .setxattr    = fuse_adapter_setxattr,
    .getxattr    = fuse_adapter_getxattr,
    .listxattr   = fuse_adapter_listxattr,
    .removexattr = fuse_adapter_removexattr,

	.readdir	 = fuse_adapter_readdir,
	.releasedir	 = fuse_adapter_releasedir,
	.fsyncdir	 = fuse_adapter_fsyncdir,
    
	.init        = fuse_adapter_init,
	.destroy     = fuse_adapter_destroy,

    .access     = fuse_adapter_access,
    .create     = fuse_adapter_create,
    // .lock       = fuse_adapter_lock,
    .utimens    = fuse_adapter_utimens,

    .fallocate  = fuse_adapter_fallocate,
    // .copy_file_range = fuse_adapter_copy_file_range,
    .lseek      = fuse_adapter_lseek,
};
int main(int argc, char *argv[])
{
	int ret = 0;
	struct fuse_args args = FUSE_ARGS_INIT(argc, argv);

    /* This is required so that the fuse_opt_parse below can free on error. */
	fuse_adapter_options.path = strdup("");
	fuse_adapter_options.log_path = strdup("");

	if (fuse_opt_parse(&args,
                       &fuse_adapter_options,
                       (struct fuse_opt *)&fuse_adapter_options_spec,
                       NULL) == -1) {
		return 1;
    }
    if (fuse_adapter_options.loopback) {
		printf("Loopback is ENABLED\n");
	}
	/* With --help, print our help, followed by standard fuse help. */
	if (fuse_adapter_options.help) {
		printf("%s: [--path=device] [--help] [--log_path=path] \n", argv[0]);
		fuse_opt_add_arg(&args, "--help");
		args.argv[0][0] = '\0';
	}

	ret = fuse_main(args.argc, args.argv, &fuse_adapter_ops, NULL);
    fuse_opt_free_args(&args);
	return ret;
}
