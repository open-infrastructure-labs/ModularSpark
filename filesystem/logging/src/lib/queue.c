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
#include "queue.h"

void queue_init(queue_t *q)
{
    q->head = (queue_node_t *)q;
    q->tail = (queue_node_t *)q;
}

bool queue_is_empty(queue_t *q)
{
    return (q->head == (queue_node_t*)q);
}

void queue_insert(queue_t *q, queue_node_t *node)
{
    if (q->head == (queue_node_t*)q) {
        q->head = node;
        q->tail = node;
        node->next = (queue_node_t*)q;
        node->prev = (queue_node_t*)q;
    } else {
        node->prev = q->tail;
        node->next = ((queue_node_t *)q->tail)->next;
        ((queue_node_t *)q->tail)->next = node;
        q->tail = node;
    }
}


void queue_remove(queue_t *q, queue_node_t *node)
{
    if (!queue_is_empty(q)) {
        ((queue_node_t*)((queue_node_t*)node)->prev)->next = node->next;
        ((queue_node_t*)((queue_node_t*)node)->next)->prev = node->prev;
    }
}
queue_node_t * queue_head(queue_t *q)
{
    return q->head;
}
queue_node_t * queue_pop(queue_t *q)
{
    if (!queue_is_empty(q)) {
        queue_node_t *head = q->head;
        queue_remove(q, head);
        return head;
    } else {
        return NULL;
    }
}

