#
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

# Inspired by:
# https://github.com/tensorflow/docs/blob/master/site/en/tutorials/distribute/multi_worker_with_keras.ipynb

import os
import json

import tensorflow as tf
import mnist_setup


model_path = '/tmp/keras-model'


def _is_chief(task_type, task_id):
  # Note: there are two possible `TF_CONFIG` configurations.
  #   1) In addition to `worker` tasks, a `chief` task type is use;
  #      in this case, this function should be modified to
  #      `return task_type == 'chief'`.
  #   2) Only `worker` task type is used; in this case, worker 0 is
  #      regarded as the chief. The implementation demonstrated here
  #      is for this case.
  # For the purpose of this Colab section, the `task_type` is `None` case
  # is added because it is effectively run with only a single worker.
  return (task_type == 'worker' and task_id == 0) or task_type is None

def _get_temp_dir(dirpath, task_id):
  base_dirpath = 'workertemp_' + str(task_id)
  temp_dir = os.path.join(dirpath, base_dirpath)
  tf.io.gfile.makedirs(temp_dir)
  return temp_dir

def write_filepath(filepath, task_type, task_id):
  dirpath = os.path.dirname(filepath)
  base = os.path.basename(filepath)
  if not _is_chief(task_type, task_id):
    dirpath = _get_temp_dir(dirpath, task_id)
  return os.path.join(dirpath, base)



per_worker_batch_size = 64
# tf_config = {
#     'cluster': {
#         'worker': ['localhost:12345', 'localhost:12346', 'localhost:12347', 'localhost:12348',
#                    'localhost:12349', 'localhost:123150', 'localhost:12351', 'localhost:12352']
#     },
#     'task': {'type': 'worker', 'index': 0}
# }
# tf_config_json = json.dumps(tf_config)
tf_config = json.loads(os.environ['TF_CONFIG'])
num_workers = len(tf_config['cluster']['worker'])
print(f"num_workers: {num_workers}")
strategy = tf.distribute.MultiWorkerMirroredStrategy()

global_batch_size = per_worker_batch_size * num_workers
multi_worker_dataset = mnist_setup.mnist_dataset(global_batch_size)

with strategy.scope():
  # Model building/compiling need to be within `strategy.scope()`.
  multi_worker_model = mnist_setup.build_and_compile_cnn_model()


  multi_worker_model.fit(multi_worker_dataset, epochs=3, steps_per_epoch=70)

  task_type, task_id = (strategy.cluster_resolver.task_type,
                        strategy.cluster_resolver.task_id)
  write_model_path = write_filepath(model_path, task_type, task_id)
  print(f"{task_type}-{task_id} -> {write_model_path}")
  multi_worker_model.save(write_model_path)