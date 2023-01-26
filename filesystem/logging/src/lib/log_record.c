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
#define _GNU_SOURCE // For gettid and sched_getcpu()
#include <stdio.h>
#include <stdlib.h> // for malloc/free
#include <stdarg.h>
#include <unistd.h> // for gettid(), getpid()
#include <string.h>
#include "log_service_local.h"

// Intentionally holds the context lock on exit.
log_record_t *log_get_record(log_context_t *context)
{
    log_record_t *rec = NULL;

    log_context_lock(context);
    
    /* Get the trace record to use.
     * Check if we need to wait for a buffer to free.
     */
    while ((context->wait_count != 0) ||
           (rec = log_context_get_record(context)) == NULL) {
        context->num_waits++;
        // fprintf(stderr, "logger_record waited for records on core [%u]. total waits: %lu\n",
        //         core_id, context->num_waits);
        log_context_unlock(context);

        // Keep lock order of service lock, context lock.
        log_service_lock();
        log_context_lock(context);
        context->wait_count++;
        log_thread_signal();
        log_context_unlock(context);
        log_service_unlock();

        debug_trace("[%u] sem_wait\n", context->core_id);
        /* Wait for wakeup by log thread after buffer available.*/
        sem_wait(&context->buffer_sem);
        log_context_lock(context);
    } 
    return rec;
}
  
void log_record_fill_header(log_record_t *rec, uint32_t core_id, log_opcode_t op)
{
    /* Fill the record. */
    rec->core = core_id;

    /* Fill with a timestamp. */
    struct timespec now;
    clock_gettime(CLOCK_REALTIME, &now);
    rec->sec = now.tv_sec;
    rec->nsec = now.tv_nsec;

    /* Fill out the record with thread/process IDs. */
    rec->pid = getpid();
    rec->tid = gettid();

    rec->opcode = op;
}

// Assumes the context lock is held.
void log_finish(log_context_t *context)
{
    /* If the buffer is full, flush it.*/
    if (context->traces_remaining == 0) {
        debug_trace("[%u] Buffer is full, enqueue for flush.\n", context->core_id);        
        context->current_buffer->valid_bytes = LOG_THREAD_BUFFER_RECORD_BYTES;
        log_header_check_magic(context->current_buffer);
        queue_insert(&context->flush_buffer_queue, &context->current_buffer->queue_node);
        context->current_buffer = NULL;
        log_context_unlock(context);
        log_service_lock();
        log_thread_signal();
        log_service_unlock();
    } else {
        log_context_unlock(context);
    }
}

static void log_file_get_hash(const char *filename, uint8_t *hash)
{
    if (filename != NULL) {
        SHA256_CTX sha256;

        SHA256_Init(&sha256);
        SHA256_Update(&sha256, filename, strlen(filename));
        SHA256_Final(hash, &sha256);
    } else {
        memset(hash, 0, SHA256_DIGEST_LENGTH);
    }
}
void logger_record_generic(log_opcode_t op,
                           const char *filename,
                           uint64_t handle,
                           unsigned long arg0, unsigned long arg1, unsigned long arg2, unsigned long arg3)
{
    if (!log_service_flag_is_set(LOG_SERVICE_FLAGS_INIT)) {
        return;
    }
    log_record_t *rec = NULL;
    int core_id = sched_getcpu();
    log_context_t *context = log_get_context(core_id);
    rec = log_get_record(context);

    if (rec == NULL) {
        fprintf(stderr, "log service could not get record.\n");
        return;
    }
    log_record_fill_header(rec, core_id, op);

    log_file_get_hash(filename, &rec->data.generic.file_hash[0]);
    rec->data.generic.handle = handle;

    /* Fill out the record with The trace content. */
    rec->data.generic.arg0 = arg0;
    rec->data.generic.arg1 = arg1;
    rec->data.generic.arg2 = arg2;
    rec->data.generic.arg3 = arg3;
    
    log_finish(context);
}
void log_get_filename(const char *filename, char *saved)
{
    int len = strlen(filename);    
    const char *file_to_save = filename;

    if (len > LOG_MAX_FILE_CHARS) {
        int offset = len - LOG_MAX_FILE_CHARS;
        len = LOG_MAX_FILE_CHARS;
        file_to_save += offset;
    }
    strncpy(saved, file_to_save, len);
}

void logger_record_open(const char *filename,
                        uint32_t flags,
                        uint64_t handle)
{
    if (!log_service_flag_is_set(LOG_SERVICE_FLAGS_INIT)) {
        // fprintf(stderr, "log service not initialized\n");
        return;
    }
    log_opcode_t op = LOG_OPCODE_OPEN;                        
    log_record_t *rec = NULL;
    int core_id = sched_getcpu();
    log_context_t *context = log_get_context(core_id);
    rec = log_get_record(context);

    if (rec == NULL) {
        fprintf(stderr, "log service could not get record.\n");
        return;
    }
    log_record_fill_header(rec, core_id, op);

    /* Fill out the record with The trace content. */
    log_file_get_hash(filename, &rec->data.open.file_hash[0]);
    log_get_filename(filename, &rec->data.open.filename[0]);
    rec->data.open.flags = flags;
    rec->data.open.handle = handle;
    
    log_finish(context);
}

void logger_record_rw(log_opcode_t op,
                      uint64_t handle,
                      const char *filename,
                      uint64_t offset,
                      uint64_t length)
{
    if (!log_service_flag_is_set(LOG_SERVICE_FLAGS_INIT)) {
        // fprintf(stderr, "log service not initialized\n");
        return;
    }
    log_record_t *rec = NULL;
    int core_id = sched_getcpu();
    log_context_t *context = log_get_context(core_id);
    rec = log_get_record(context);

    if (rec == NULL) {
        fprintf(stderr, "log service could not get record.\n");
        return;
    }
    log_record_fill_header(rec, core_id, op);

    /* Fill out the record with The trace content. */
    log_file_get_hash(filename, &rec->data.rw.file_hash[0]);
    rec->data.rw.offset = offset;
    rec->data.rw.length = length;
    
    log_finish(context);
}
