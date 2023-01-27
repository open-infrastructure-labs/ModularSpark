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
#define _GNU_SOURCE // For sched.h (sched_getcpu())
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "log_service_local.h"


bool log_context_flag_is_set(log_context_t *context, log_context_flags_t flags)
{
    return ((context->flags & flags) == flags);
}
void log_context_flag_set(log_context_t *context, log_context_flags_t flags)
{
    context->flags |= flags;
}
void log_context_flag_clear(log_context_t *context, log_context_flags_t flags)
{
    context->flags &= ~flags;
}
void log_context_lock(log_context_t *context)
{
    pthread_mutex_lock(&context->mutex);
}
void log_context_unlock(log_context_t *context)
{
    pthread_mutex_unlock(&context->mutex);
}
bool log_header_check_magic(log_buffer_header_t *header)
{
    if (header->magic != LOG_MAGIC)
    {
        fprintf(stderr, "magic number check failed\n");
        return false;
    }
    return true;
}

bool log_context_allocate_buffer(log_context_t *context)
{
    if (!queue_is_empty(&context->free_buffer_queue)) {
        log_header_check_magic((log_buffer_header_t*)context->free_buffer_queue.head);
        log_buffer_header_t *buffer = (log_buffer_header_t*) queue_pop(&context->free_buffer_queue);        
        context->traces_remaining = LOG_RECORDS_PER_BUFFER;
        context->current_buffer = buffer;
        context->current_record = &context->current_buffer->records[0];
        return true;
    } else {
        return false;
    }
}

void log_context_init(log_context_t *context, uint32_t core_id)
{
    context->core_id = core_id;
    context->file = NULL;
    sem_init(&context->buffer_sem, 0, /* Not shared. */ 0);
    log_context_flag_set(context, LOG_CORE_CONTEXT_FLAGS_INITTED);

    uint32_t buffer_bytes = LOG_CORE_CONTEXT_BUFFER_COUNT * LOG_THREAD_BUFFER_BYTES;

    uint8_t *buffer = (uint8_t*)malloc(buffer_bytes);
    context->buffers = (log_buffer_header_t *)buffer;
    int i;
    queue_init(&context->flush_buffer_queue);
    queue_init(&context->free_buffer_queue);
    for (i = 0;  i < LOG_CORE_CONTEXT_BUFFER_COUNT; i++) {
        log_buffer_header_t *header = (log_buffer_header_t *)buffer;
        header->valid_bytes = 0;
        header->magic = LOG_MAGIC;
        queue_insert(&context->free_buffer_queue, &header->queue_node);
        buffer += LOG_THREAD_BUFFER_BYTES;
    }
    log_context_allocate_buffer(context);
}

log_record_t * log_context_get_record(log_context_t *context)
{
    if (context->current_buffer != NULL) {
        log_record_t * rec = context->current_record;
        if ((context->traces_remaining == 0) ||
            (context->traces_remaining > LOG_RECORDS_PER_BUFFER)) {
            fprintf(stderr, "traces remaining invalid %u\n", context->traces_remaining);
        }
        context->traces_remaining--;
        context->current_record++;
        return rec;
    } else {
        return NULL;
    }
}
void log_context_open_file(log_context_t *context)
{
    if (context->file == NULL) {
        char filename[PATH_MAX];
        sprintf(filename, "%s/log_core_%u.bin", log_service_get_log_path(), context->core_id);
        context->file = fopen(filename, "w");

        if (context->file == NULL) {
            fprintf(stderr, "failed to open file: %s\n", filename);
        }
    }
}

void log_context_start_flush(log_context_t *context)
{
    // Assumes that the service lock is held.
    // By holding service lock and context lock, we ensure that the
    // thread will run a full loop to process our event.

    log_context_lock(context);
    /* Only flush if the buffer is not empty.
     */
    if ((context->current_buffer != NULL) &&
        (context->traces_remaining != LOG_RECORDS_PER_BUFFER)) {
        debug_trace("[%u] Enqueue for flush.\n", context->core_id);
        if (context->traces_remaining == 0) {
            context->current_buffer->valid_bytes = LOG_THREAD_BUFFER_RECORD_BYTES;
        } else {
            context->current_buffer->valid_bytes = LOG_THREAD_BUFFER_RECORD_BYTES -
                                                   (context->traces_remaining * sizeof(log_record_t));
        }
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

void log_flush_context(log_context_t *context)
{
    queue_node_t *node = NULL;

    log_context_open_file(context);
    if (context->file == NULL) {
        fprintf(stderr, "Cannot flush, unable to open file\n");
        return;
    }
    
    while ((node = queue_pop(&context->flush_buffer_queue)) != NULL) {
        
        log_buffer_header_t *header = (log_buffer_header_t*)node;
        log_header_check_magic(header);
        debug_trace("[%u] flushing %u bytes of buffer %p\n",
                    context->core_id, header->valid_bytes, node);
        if (header->valid_bytes > 0) {
            int bytes = fwrite(&header->records[0], 1, header->valid_bytes, context->file);
            if (bytes != header->valid_bytes) {
                fprintf(stderr, "[%u] error writing bytes != %u\n", 
                        context->core_id, header->valid_bytes);
            }
        }
        queue_insert(&context->free_buffer_queue, node);
    }
    if (context->current_buffer == NULL) {
        log_context_allocate_buffer(context);
    }
}