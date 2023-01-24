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
#include "log_service_local.h"

static log_service_t log_service;

static void *log_thread(void *unused);

bool log_service_flag_is_set(log_service_t *context, log_service_flags_t flags)
{
    return ((context->flags & flags) == flags);
}
void log_service_flag_set(log_service_t *context, log_service_flags_t flags)
{
    context->flags |= flags;
}
void log_service_flag_clear(log_service_t *context, log_service_flags_t flags)
{
    context->flags &= ~flags;
}
log_context_t * log_get_context(uint32_t core)
{
    return &log_service.core_context[core];
}

void log_service_lock(void)
{
    pthread_mutex_lock(&log_service.mutex);
}
void log_service_unlock(void)
{
    pthread_mutex_unlock(&log_service.mutex);
}

void logger_init(void)
{
    log_service.cores = sysconf(_SC_NPROCESSORS_ONLN);
    log_service.core_context = (log_context_t*)malloc(log_service.cores * sizeof(log_context_t));
    if (log_service.core_context == NULL) {
        fprintf(stderr, "unable to allocate core_context");
        return;
    }
    uint32_t core_id;
    for (core_id = 0; core_id < log_service.cores; core_id++){
        log_context_init(log_get_context(core_id), core_id);
    }
    log_service_flag_set(&log_service, LOG_SERVICE_FLAGS_INIT);
    pthread_mutex_init(&log_service.mutex, NULL);
    pthread_cond_init(&log_service.cond, NULL);
    pthread_create(&log_service.thread, NULL, log_thread, &log_service);
}

// Thread for flushing traces to file in the background.
static void *log_thread(void *unused)
{
    printf("log_service starting\n");
    while (!log_service_flag_is_set(&log_service, LOG_SERVICE_FLAGS_HALT)) {
        log_service_lock();
        uint32_t core;
        for (core = 0; core < log_service.cores; core++) {
            // printf("[%u] flush thread run\n", core);
            log_context_t *context = log_get_context(core);
            log_context_lock(context);
            if (!queue_is_empty(&context->flush_buffer_queue)) {
                log_flush_context(context);
            }
            if (context->wait_count > 0) {
                debug_trace("[%u] wait_count: %u\n", core, context->wait_count);
                // debug_trace("[%u] wait_count: %u\n", core, context->wait_count);
                int i;
                for (i = 0; i < context->wait_count; i++) {
                    sem_post(&context->buffer_sem);
                    debug_trace("[%u] post\n", core);
                }
                context->wait_count = 0;
            }
            log_context_unlock(context);
        }
        pthread_cond_wait(&log_service.cond, &log_service.mutex);
        log_service_unlock();
    }
    printf("log_service exiting\n");
    return NULL;
}
void log_thread_signal(void)
{
    debug_trace("[%u] flush thread signal\n", sched_getcpu());
    pthread_cond_signal(&log_service.cond);
}

void logger_record(const char *format,
                   unsigned long arg0, unsigned long arg1, unsigned long arg2, unsigned long arg3)
{
    if (!log_service_flag_is_set(&log_service, LOG_SERVICE_FLAGS_INIT)) {
        fprintf(stderr, "log service not initialized\n");
        return;
    }
    log_record_t *rec = NULL;
    int core_id = sched_getcpu();
    log_context_t *context = log_get_context(core_id);
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

        debug_trace("[%u] sem_wait\n", core_id);
        /* Wait for wakeup by log thread after buffer available.*/
        sem_wait(&context->buffer_sem);
        log_context_lock(context);
    }
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

    /* Fill out the record with The trace content. */
    rec->arg0 = arg0;
    rec->arg1 = arg1;
    rec->arg2 = arg2;
    rec->arg3 = arg3;
    
    // debug_trace(format, arg0, arg1, arg2, arg3);

    /* If the buffer is full, flush it.*/
    if (context->traces_remaining == 0) {
        debug_trace("[%u] Buffer is full, enqueue for flush.\n", core_id);        
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

// If traces need to be flushed, returns true.
bool logger_is_flush_needed(void)
{
    bool needed = false;
    uint32_t core_id;
    log_context_t *context = NULL;
    for (core_id = 0; core_id < log_service.cores; core_id++){
        context = log_get_context(core_id);
        log_context_lock(context);
        if (!queue_is_empty(&context->flush_buffer_queue)) {
            needed = true;
            log_context_unlock(context);
            break;
        }
        log_context_unlock(context);
    }
    return needed;
}

// Flush out all the buffers that need it.
void logger_flush(void)
{
    debug_trace("[%u] Flush started\n", sched_getcpu());

    uint32_t core_id;
    for (core_id = 0; core_id < log_service.cores; core_id++) {
        log_context_start_flush(log_get_context(core_id));
    }
}

#if 0
#define DEBUG_REC_COUNT (1024*1024)
log_debug_rec_t debug_rec[1024*1024];
uint64_t rec_index = 0;
void debug_trace(const char* format, ...)
{
    log_debug_rec_t *rec = &debug_rec[rec_index];
    va_list argptr;
    va_start(argptr, format);
    vsprintf(&rec->log[0], format, argptr);
    va_end(argptr);
    rec_index++;
    if (rec_index > DEBUG_REC_COUNT) {
        rec_index = 0;
    }
}
#elif 0
void debug_trace(const char* format, ...)
{
    va_list argptr;
    va_start(argptr, format);
    vfprintf(stderr, format, argptr);
    va_end(argptr);
    fflush(stdin);
}
#endif