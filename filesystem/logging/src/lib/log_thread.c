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
#include <string.h>
#include <stdbool.h>
#include <pthread.h>
#include <stdlib.h>
#include <unistd.h>
#include <sched.h>
#include <stdarg.h>
#include <fcntl.h>
#include <time.h>
#include <sys/time.h>
#include "log_service_local.h"


void *log_service_flush_thread(void *unused)
{
    printf("log_service starting\n");
    while (!log_service_flag_is_set(&log_service, LOG_SERVICE_FLAGS_HALT)) {
        pthread_mutex_lock(&log_service.mutex);
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
        pthread_mutex_unlock(&log_service.mutex);
    }
    printf("log_service exiting\n");
    return NULL;
}
void log_thread_signal(void)
{
    debug_trace("[%u] flush thread signal\n", sched_getcpu());
    pthread_cond_signal(&log_service.cond);
}