#ifndef __LOG_FLUSH_H__
#define __LOG_FLUSH_H__
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
#include <pthread.h>
#include <semaphore.h>
#include <stdint.h>
#include <openssl/sha.h>
#include <linux/limits.h>
#include "logger.h"
#include "queue.h"

enum {
    LOG_FLUSH_WAIT_SEC = 2,
    LOG_MAX_FILE_CHARS = 64,
    LOG_CORE_CONTEXT_BUFFER_COUNT = 2,
    LOG_THREAD_DEFAULT_BUFFER_MB = 10,
};

#pragma pack(1)
typedef struct log_record_s {
    uint16_t core;
    uint8_t  opcode;
    uint8_t  unused[5];

    pid_t    pid;
    pid_t    tid;

    uint64_t sec;
    uint64_t nsec;

    union {
        struct {
            uint8_t  file_hash[SHA256_DIGEST_LENGTH];
            uint64_t handle;
            char     filename[LOG_MAX_FILE_CHARS];
            uint32_t flags;
            uint32_t unused_1;
        } open;
        struct {
            uint8_t  file_hash[SHA256_DIGEST_LENGTH];
            uint64_t handle;
            uint64_t offset;
            uint64_t length;
        } rw;
        struct {
            uint8_t  file_hash[SHA256_DIGEST_LENGTH];
            uint64_t handle;
            uint64_t arg0;
            uint64_t arg1;
            uint64_t arg2;
            uint64_t arg3;
        } generic;
    }
    data;
} log_record_t;
#pragma pack()

typedef struct log_buffer_header_s {
    queue_node_t queue_node;
    uint64_t magic;
    uint32_t valid_bytes; /* Bytes in the buffer valid for flushing. */
    log_record_t records[0];
} log_buffer_header_t;

#define LOG_MAGIC 0x1111111122222222L
#define LOG_RECORDS_PER_MB \
 ((1024 * 1024) / sizeof(log_record_t) )

#define LOG_RECORDS_PER_BUFFER \
 (LOG_RECORDS_PER_MB * LOG_THREAD_DEFAULT_BUFFER_MB)

#define LOG_THREAD_BUFFER_BYTES     \
 ((LOG_RECORDS_PER_BUFFER * sizeof(log_record_t)) + sizeof(log_buffer_header_t))

 #define LOG_THREAD_BUFFER_RECORD_BYTES     \
 (LOG_RECORDS_PER_BUFFER * sizeof(log_record_t))

typedef enum log_context_flags_s {
    LOG_CORE_CONTEXT_FLAGS_INVALID = 0x0000,
    LOG_CORE_CONTEXT_FLAGS_INITTED = 0x0001,
    LOG_CORE_CONTEXT_FLAGS_WAITING = 0x0002,
} log_context_flags_t;

typedef struct log_context_s {
    queue_node_t        node;
    uint32_t            core_id;
    log_context_flags_t flags;
    pthread_mutex_t     mutex;

    sem_t                buffer_sem;
    uint32_t             wait_count;
    uint64_t             num_waits;
    log_buffer_header_t *buffers;
    queue_t              free_buffer_queue;
    queue_t              flush_buffer_queue;

    log_buffer_header_t *current_buffer;
    log_record_t        *current_record;
    uint32_t             traces_remaining;

    FILE                *file;
} log_context_t; 

typedef enum log_service_flags_s {
    LOG_SERVICE_FLAGS_INVALID = 0x0000,
    LOG_SERVICE_FLAGS_INIT = 0x0001,
    LOG_SERVICE_FLAGS_HALT = 0x0002,
} log_service_flags_t;

typedef struct log_thread_s {
    pthread_cond_t      cond;
    pthread_mutex_t     mutex;
    log_service_flags_t flags;
    pthread_t           thread;
    long                cores;
    log_context_t      *core_context;
    char                log_path[PATH_MAX];
    pthread_mutex_t     debug_log_mutex;
    char                debug_log_path[PATH_MAX];
    FILE *              debug_file;
} log_service_t;

/* A debug record for debug tracing. */
#pragma pack(1)
typedef struct log_debug_rec_s {
    char log[128];
} log_debug_rec_t;
#pragma pack()

log_context_t * log_get_context(uint32_t core);
void log_context_lock(log_context_t *context);
void log_context_unlock(log_context_t *context);
void log_context_init(log_context_t *context, uint32_t core_id);
log_record_t * log_context_get_record(log_context_t *context);
void log_flush_context(log_context_t *context);
void log_context_start_flush_bg(log_context_t *context);



bool log_context_allocate_buffer(log_context_t *context);
void log_context_start_flush(log_context_t *context);
void log_context_start_flush_bg(log_context_t *context);
bool log_context_is_flag_set(log_context_t *context, log_context_flags_t flags);
bool log_header_check_magic(log_buffer_header_t *header);

log_service_t *log_get_service(void);
bool log_service_flag_is_set(log_service_flags_t flags);
void log_service_flag_set(log_service_flags_t flags);
void log_service_flag_clear(log_service_flags_t flags);
char *log_service_get_log_path(void);
void log_service_lock(void);
void log_service_unlock(void);
void log_thread_signal(void);

// Uncomment the below for verbose tracing.
// #define LOG_DEBUG 1
#define LOG_DEBUG 0
#if LOG_DEBUG
void debug_trace(const char *__restrict __fmt, ...);
#else
#define debug_trace(...) ((void)0)
#endif

#endif