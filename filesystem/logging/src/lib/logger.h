#ifndef __LOGGER_H__
#define __LOGGER_H__
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
 
#include <stdio.h>
#include <stdbool.h>

#define LOG_HANDLE_INVALID 0xFFFFFFFF

typedef enum log_opcode_e {
    LOG_OPCODE_INVALID,

    LOG_OPCODE_GETATTR,
    LOG_OPCODE_READLINK,

    LOG_OPCODE_MKNOD,
    LOG_OPCODE_MKDIR,
    LOG_OPCODE_UNLINK,
    LOG_OPCODE_RMDIR,

    LOG_OPCODE_SYMLINK,
    LOG_OPCODE_RENAME,
    LOG_OPCODE_LINK,

    LOG_OPCODE_CHMOD,
    LOG_OPCODE_CHOWN,
    LOG_OPCODE_TRUNCATE,

    LOG_OPCODE_OPEN,
    LOG_OPCODE_READ,
    LOG_OPCODE_WRITE,
    LOG_OPCODE_STATFS,

    LOG_OPCODE_FLUSH,
    LOG_OPCODE_RELEASE,
    LOG_OPCODE_FSYNC,

    LOG_OPCODE_SETXATTR,
    LOG_OPCODE_GETXATTR,
    LOG_OPCODE_LISTXATTR,
    LOG_OPCODE_REMOVEXATTR,

    LOG_OPCODE_READDIR,
    LOG_OPCODE_RELEASEDIR,
    LOG_OPCODE_FSYNCDIR,

    LOG_OPCODE_INIT,
    LOG_OPCODE_DESTROY,

    LOG_OPCODE_ACCESS,
    LOG_OPCODE_CREATE,
    LOG_OPCODE_UTIMENS,
    
    LOG_OPCODE_FALLOCATE,
    LOG_OPCODE_LSEEK,
    
    LOG_OPCODE_MAX,
    
} log_opcode_t;

void logger_init(const char *log_path);
void logger_record_generic(log_opcode_t op,
                           const char *filename,
                           uint64_t handle,
                           unsigned long arg0, unsigned long arg1, unsigned long arg2, unsigned long arg3);
void logger_record_open(const char *filename,
                        uint32_t flags,
                        uint64_t handle);
void logger_record_rw(log_opcode_t op,
                      uint64_t handle,
                      const char *filename,
                      uint64_t offset,
                      uint64_t length);
void logger_flush(void);
bool logger_is_flush_needed(void);
#endif