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
# limitations under the License.import numpy as np

# Inspired by:
# Taken from https://github.com/aqibsaeed/sensor-transformer

import os.path
import numpy as np
from sensortransformer import set_network
from spark_tensorflow_distributor import MirroredStrategyRunner
from pyspark.sql import SparkSession

def train_and_eval():
    import tensorflow as tf

    BATCH_SIZE, BUFFER_SIZE = 100, 1000
    def make_datasets():
        segments = np.load('segments.npy')
        labels = np.load('labels.npy')

        segments = segments.astype('float32')
        labels = labels.astype('float32')
        reshaped_segments = segments

        train_test_split = np.random.rand(len(reshaped_segments)) < 0.7
        train_x = reshaped_segments[train_test_split]
        train_y = labels[train_test_split]
        test_x = reshaped_segments[~train_test_split]
        test_y = labels[~train_test_split]

        signal_length = train_x.shape[1]
        channels = train_x.shape[2]
        num_classes = train_y.shape[1]

        train_dataset = tf.data.Dataset.from_tensor_slices((train_x, train_y))
        train_dataset = train_dataset.shuffle(buffer_size=BUFFER_SIZE, reshuffle_each_iteration=True)
        train_dataset = train_dataset.batch(batch_size=BATCH_SIZE).prefetch(tf.data.experimental.AUTOTUNE)

        test_dataset = tf.data.Dataset.from_tensor_slices((test_x, test_y))
        test_dataset = test_dataset.batch(batch_size=BATCH_SIZE).prefetch(tf.data.experimental.AUTOTUNE)

        return (train_dataset, test_dataset, signal_length, channels, num_classes)

    def build_and_compile_model(signal_length, channels, num_classes):
        model = set_network.SensorTransformer(
            signal_length=signal_length,
            segment_size=10,
            channels=channels,
            num_classes=num_classes,
            num_layers=4,
            d_model=64,
            num_heads=4,
            mlp_dim=64,
            dropout=0.1,
        )
        model.compile(
            loss=tf.keras.losses.CategoricalCrossentropy(from_logits=True),
            optimizer=tf.keras.optimizers.Adam(),
            metrics=[tf.keras.metrics.CategoricalAccuracy()],
        )
        return model

    model_path = '/tmp/iot-model-1'

    def _is_chief(task_type, task_id):
        return (task_type=='worker' and task_id==0) or task_type is None

    def _get_temp_dir(dirpath, task_id):
        base_dirpath = 'workertemp_' + str(task_id)
        temp_dir = os.path.join(dirpath, base_dirpath)
        tf.io.gfile.makedirs(temp_dir)

    def write_filepath(filepath, task_type, task_id):
        dirpath = os.path.dirname(filepath)
        base = os.path.basename(filepath)
        if not _is_chief(task_type, task_id):
            dirpath = _get_temp_dir(dirpath, task_id)
        return os.path.join(dirpath, base)

    train_dataset, test_dataset, signal_length, channels, num_classes = make_datasets()
    options = tf.data.Options()
    options.experimental_distribute.auto_shard_policy = tf.data.experimental.AutoShardPolicy.DATA
    train_dataset = train_dataset.with_options(options)
    model = build_and_compile_model(signal_length, channels, num_classes)
    task_id = model.distribute_strategy.cluster_resolver.task_id
    task_type = model.distribute_strategy.cluster_resolver.task_type
    print(f'start fitting {task_type} {task_id}')
    model.fit(train_dataset, epochs=50, verbose=1)
    print(f'start evaluting {task_type} {task_id}')
    model.evaluate(test_dataset)
    print(f'done {task_type} {task_id}')

    print(f'saving model for {task_type} {task_id}')
    write_model_path = write_filepath(model_path, task_type, task_id)
    model.save(write_model_path, overwrite=True)
    print(f'saving model compute for {task_type} {task_id}')

print('starting training and evaluating')
iot_model = MirroredStrategyRunner(num_slots=8, use_gpu=False, local_mode=False).run(train_and_eval)
print('done training and evaluating')
