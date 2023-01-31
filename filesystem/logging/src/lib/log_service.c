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

static log_service_t log_service;

static void *log_thread(void *unused);

log_service_t *log_get_service(void)
{
    return &log_service;
}

bool log_service_flag_is_set(log_service_flags_t flags)
{
    log_service_t *svc = log_get_service();
    return ((svc->flags & flags) == flags);
}
void log_service_flag_set(log_service_flags_t flags)
{
    log_service_t *svc = log_get_service();
    svc->flags |= flags;
}
void log_service_flag_clear(log_service_flags_t flags)
{
    log_service_t *svc = log_get_service();
    svc->flags &= ~flags;
}
log_context_t * log_get_context(uint32_t core)
{
    return &log_service.core_context[core];
}
char *log_service_get_log_path(void)
{
    return &log_service.log_path[0];
}
void log_service_lock(void)
{
    pthread_mutex_lock(&log_service.mutex);
}
void log_service_unlock(void)
{
    pthread_mutex_unlock(&log_service.mutex);
}

void logger_init(const char *log_path)
{
    if (log_service_flag_is_set(LOG_SERVICE_FLAGS_INIT)) {
        return;
    }
    printf("logging service initialize\n");
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
    log_service_flag_set(LOG_SERVICE_FLAGS_INIT);
    pthread_mutex_init(&log_service.mutex, NULL);
    pthread_cond_init(&log_service.cond, NULL);
    pthread_create(&log_service.thread, NULL, log_thread, &log_service);

    if (log_path != NULL && strlen(log_path) != 0) {
        // Use user supplied path. 
        strncpy(log_service_get_log_path(), log_path, strlen(log_path));
    } else {
        // Use the current path for files.
        getcwd(log_service_get_log_path(), PATH_MAX);
    }
    printf("Logging path is: %s\n",log_service_get_log_path());
#if LOG_DEBUG
    strcpy(&log_service.debug_log_path[0], log_service_get_log_path());
    strcat(&log_service.debug_log_path[0], "/log_debug_file.log");
    pthread_mutex_init(&log_service.debug_log_mutex, NULL);
    log_service.debug_file = fopen(&log_service.debug_log_path[0], "w");
#endif
}

// Thread for flushing traces to file in the background.
static void *log_thread(void *unused)
{
    struct timespec ts;
    struct timespec last_run_ts;
    printf("log_service starting\n");
    while (!log_service_flag_is_set(LOG_SERVICE_FLAGS_HALT)) {
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
        clock_gettime(CLOCK_REALTIME, &ts);
        last_run_ts = ts;
        ts.tv_sec += LOG_FLUSH_WAIT_SEC;
        pthread_cond_timedwait(&log_service.cond, &log_service.mutex, &ts);
        // pthread_cond_wait(&log_service.cond, &log_service.mutex);
        log_service_unlock();
        clock_gettime(CLOCK_REALTIME, &ts);
        if ((ts.tv_sec - last_run_ts.tv_sec) >= LOG_FLUSH_WAIT_SEC) {
            /* If we do a full wait without any wakeup, then check if we need to 
             * flush the buffers.  In effect, this allows us to flush the buffers
             * when we go idle.
             */
            debug_trace("Flush Timer expired.\n");
            logger_flush_background();
        }
    }
    printf("log_service exiting\n");
    return NULL;
}
void log_thread_signal(void)
{
    debug_trace("[%u] flush thread signal\n", sched_getcpu());
    pthread_cond_signal(&log_service.cond);
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
        if (!queue_is_empty(&context->flush_buffer_queue) ||
            (context->traces_remaining != LOG_RECORDS_PER_BUFFER)) {
            needed = true;
            log_context_unlock(context);
            break;
        }
        log_context_unlock(context);
    }
    return needed;
}

// A bg flush will flush out a partially full buffer,
// as long as it is not the only one remaining.
void logger_flush_background(void)
{
    uint32_t core_id;
    for (core_id = 0; core_id < log_service.cores; core_id++) {
        log_context_start_flush_bg(log_get_context(core_id));
    }
}
// Flush out all the buffers that need it.
void logger_flush(void)
{
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
#elif LOG_DEBUG
void debug_trace(const char* format, ...)
{
    if (!log_service_flag_is_set(LOG_SERVICE_FLAGS_INIT)) {
        return;
    }
    pthread_mutex_lock(&log_service.debug_log_mutex);
    va_list argptr;
    va_start(argptr, format);
    vfprintf(log_service.debug_file, format, argptr);
    va_end(argptr);
    fflush(log_service.debug_file);
    pthread_mutex_unlock(&log_service.debug_log_mutex);
}
#endif