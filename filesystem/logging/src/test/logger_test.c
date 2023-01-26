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
#define _GNU_SOURCE
#include <pthread.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdlib.h>
#include <math.h>
#include "../lib/logger.h"
#include "../lib/log_service_local.h"

void wait_for_flush(void)
{
    while (logger_is_flush_needed()) {
        printf("Waiting for flush of log\n");
        sleep(1);
    }
}
void logger_test(void)
{
    const uint32_t messages = 40;
    uint32_t i;
    uint64_t val = 1;

    logger_init();

    uint64_t offset = 0;
    uint64_t len = 1024;
    for (i = 0; i < messages; i++) {
        uint64_t handle = 0x9876543200000000L | i;
        logger_record_open("filename.txt", 0x1234 | i, handle);
        logger_record_rw(LOG_OPCODE_WRITE, handle, "filename.txt", offset, len);
        logger_record_rw(LOG_OPCODE_READ, handle, "filename.txt", offset, len);
        logger_record_generic(LOG_OPCODE_FLUSH, "foo", 99,
                              i, val + 1, val + 2, val + 3);
    }

    logger_flush();
    wait_for_flush();
}

typedef struct test_param_s {
    uint32_t thread;
    uint32_t message_count;
    uint32_t affine_group;
} test_param_t;

static void *logger_test_thread(void *param)
{
    test_param_t *params = (test_param_t*) param;
    printf("test thread %u started\n", params->thread);

    if (params->affine_group > 0) {
        cpu_set_t cpuset;
        CPU_ZERO(&cpuset);
        CPU_SET(1 + (params->thread % 3), &cpuset);

        pthread_t current_thread = pthread_self();    
        pthread_setaffinity_np(current_thread, sizeof(cpu_set_t), &cpuset);
    }
    uint32_t i;
    for (i = 0; i < params->message_count; i++) {
        if ((i != 0) && (i % 500000) == 0) {
            printf("[%u] thread %u messages\n", params->thread, i);
        }

        logger_record_generic(LOG_OPCODE_FLUSH, "foo", params->thread,
                                params->thread, i, 2, 3);
    }
    printf("test thread %u done\n", params->thread);
    return NULL;
}

void logger_thread_test(uint32_t threads, uint64_t messages, uint32_t affine_group)
{
    test_param_t params[threads];
    pthread_t thread[threads];
    uint32_t i;
    printf("Logger thread test starting. threads:%u messages: %lu\n", threads, messages);

    for (i = 0; i < threads; i++) {
        params[i].message_count = messages;
        params[i].thread = i;
        params[i].affine_group = affine_group;
        pthread_create(&thread[i], NULL, logger_test_thread, &params[i]);
    }

    void *ret = NULL;
    for (i = 0; i < threads; i++) {
        pthread_join(thread[i], &ret);
        printf("test %u done\n", i);
    }
    
    logger_flush();
    wait_for_flush();
    printf("Logger thread test done. threads:%u messages: %lu\n", threads, messages);
    // logger_destroy();
}

void remove_log_files(void)
{
    uint32_t core_count = sysconf(_SC_NPROCESSORS_ONLN);
    uint32_t core;
    char buf[20];

    for (core = 0; core < core_count; core++) {
        sprintf(buf, "log_core_%u.bin", core);
        if (access(buf, F_OK) == 0) {
            if (remove(buf) != 0) {
                fprintf(stderr, "unable to delete file %s\n", buf);
            }
        }
    }
}

void logger_thread_tests(void)
{
    logger_init();

    /* First fill all the buffers, plus a bit more to ensure we use all buffers. */
    remove_log_files();
    // logger_thread_test(2, (LOG_RECORDS_PER_BUFFER * LOG_CORE_CONTEXT_BUFFER_COUNT) + 10);

    int threads;
    for (threads = 1; threads <= fminl(16, sysconf(_SC_NPROCESSORS_ONLN)); threads += 2) {
        remove_log_files();
        logger_thread_test(threads, (LOG_RECORDS_PER_BUFFER * 100), threads / 2);

        remove_log_files();
        logger_thread_test(threads, (LOG_RECORDS_PER_BUFFER * 100), 0);
    }
}

