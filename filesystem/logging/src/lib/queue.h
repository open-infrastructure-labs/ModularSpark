#ifndef __QUEUE_H__
#define __QUEUE_H__
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


typedef struct queue_node_s {
    struct queue_node_s *next;
    struct queue_node_s *prev;
} queue_node_t;

typedef struct queue_s {
    queue_node_t *head;
    queue_node_t *tail;
} queue_t;

void queue_init(queue_t *q);
bool queue_is_empty(queue_t *q);
void queue_insert(queue_t *q, queue_node_t *node);
void queue_remove(queue_t *q, queue_node_t *node);
void queue_test(void);
queue_node_t * queue_pop(queue_t *q);

#endif