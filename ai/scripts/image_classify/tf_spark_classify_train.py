# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Inspired by:
# https://github.com/tensorflow/docs/blob/master/site/en/tutorials/images/classification.ipynb
# https://github.com/tensorflow/ecosystem/tree/master/spark/spark-tensorflow-distributor#examples

import os
import time
import PIL
import tensorflow as tf

from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.models import Sequential
from spark_tensorflow_distributor import MirroredStrategyRunner
from pyspark.sql import SparkSession


import flower_dataset
import label_layer

num_workers = 1

def train():
  import tensorflow as tf
  tf.get_logger().setLevel('INFO')
  # strategy = tf.distribute.experimental.MultiWorkerMirroredStrategy()
  # strategy = tf.distribute.MultiWorkerMirroredStrategy()
  strategy = tf.distribute.experimental.MultiWorkerMirroredStrategy(
      tf.distribute.experimental.CollectiveCommunication.NCCL)
  with strategy.scope():
    # training code
    import uuid
    EPOCHS = 2
    BUFFER_SIZE = 10000
    img_height = 180
    img_width = 180
    per_worker_batch_size = 32
    batch_size = per_worker_batch_size * num_workers
    def get_data_augmentation():
        data_augmentation = keras.Sequential(
            [
                layers.RandomFlip("horizontal",
                                  input_shape=(img_height,
                                               img_width,
                                               3)),
                layers.RandomRotation(0.1),
                layers.RandomZoom(0.1),
            ]
        )
        return data_augmentation


    def build_and_compile_cnn_model(num_classes, class_names):
        data_augmentation = get_data_augmentation()
        model = Sequential([
            data_augmentation,
            layers.Rescaling(1. / 255, input_shape=(img_height, img_width, 3)),
            layers.Conv2D(16, 3, padding='same', activation='relu'),
            layers.MaxPooling2D(),
            layers.Conv2D(32, 3, padding='same', activation='relu'),
            layers.MaxPooling2D(),
            layers.Conv2D(64, 3, padding='same', activation='relu'),
            layers.MaxPooling2D(),
            layers.Dropout(0.2),
            layers.Flatten(),
            layers.Dense(128, activation='relu'),
            layers.Dense(num_classes),
            label_layer.LabelLimitLayer(class_names)
        ])

        model.compile(optimizer='adam',
                      loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True),
                      metrics=['accuracy'])

        model.summary()
        return model

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

    train_ds, val_ds, num_classes, class_names = flower_dataset.get_dataset(img_height, img_width, batch_size)
    options = tf.data.Options()
    options.experimental_distribute.auto_shard_policy = tf.data.experimental.AutoShardPolicy.DATA
    train_ds = train_ds.with_options(options)
    val_ds = val_ds.with_options(options)
    multi_worker_model = build_and_compile_cnn_model(num_classes, class_names)

    task_id = strategy.cluster_resolver.task_id
    task_type = strategy.cluster_resolver.task_type
    print(f"Start Fit train: {len(list(train_ds))} validate: {len(list(val_ds))} "
          f"task_type: {task_type} task_id: {task_id}")
    multi_worker_model.fit(x=train_ds, validation_data=val_ds, epochs=EPOCHS)
    print(f"Done task_type: {task_type} task_id: {task_id}")

    # Always save the model to keep all the workers in sync.
    write_model_path = write_filepath(model_path, task_type, task_id)
    print(f"Saving Model for: task_type: {task_type} task_id: {task_id} path: {write_model_path}")
    multi_worker_model.save(write_model_path, overwrite=True)
    print(f"Saving Model Complete for: task_type: {task_type} task_id: {task_id} path: {write_model_path}")

if __name__ == "__main__":
    #spark = SparkSession.builder.getOrCreate()
    #sc = spark.sparkContext
    #sc.setLogLevel("INFO")
    start_time = time.time()
    print("Starting Training")
    model = MirroredStrategyRunner(num_slots=num_workers,
                                   use_gpu=False,
                                   local_mode=(num_workers == 1),
                                   use_custom_strategy=True).run(train)
    # model = MirroredStrategyRunner(num_slots=1, use_gpu=False, local_mode=True, use_custom_strategy=True).run(train)
    end_time = time.time()
    duration = end_time - start_time
    print(f"Done training - {duration:2.2f}")

