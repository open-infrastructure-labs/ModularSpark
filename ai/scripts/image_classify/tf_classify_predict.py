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
# https://github.com/tensorflow/docs/blob/master/site/en/tutorials/images/classification.ipynb

import os
import PIL
import numpy as np
import tensorflow as tf
import flower_dataset

from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.models import Sequential
from spark_tensorflow_distributor import MirroredStrategyRunner
from pyspark.sql import SparkSession


model_path = '/tmp/keras-model'
BATCH_SIZE = 32
img_height = 180
img_width = 180

if __name__ == "__main__":
    # Load model
    # Recreate the exact same model, including its weights and the optimizer
    model = tf.keras.models.load_model(model_path)

    # Show the model architecture
    model.summary()
    config = model.get_config()
    print(config)
    class_names = config['layers'][13]['config']['labels']
    sunflower_url = "https://storage.googleapis.com/download.tensorflow.org/example_images/592px-Red_sunflower.jpg"
    sunflower_path = tf.keras.utils.get_file('Red_sunflower', origin=sunflower_url)
    img = tf.keras.utils.load_img(
        sunflower_path, target_size=(img_height, img_width)
    )
    img_array = tf.keras.utils.img_to_array(img)
    img_array = tf.expand_dims(img_array, 0)  # Create a batch
    predictions = model.predict(img_array)
    score = tf.nn.softmax(predictions[0])

    # _, _, _, class_names = flower_dataset.get_dataset(img_height, img_width, BATCH_SIZE)
    print("This image most likely belongs to {} with a {:.2f} percent confidence."
          .format(class_names[np.argmax(score)], 100 * np.max(score)))