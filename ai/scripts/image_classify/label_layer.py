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

import tensorflow as tf
from keras.layers import Layer

class LabelLimitLayer(Layer):

    def __init__(self, labels, **kwargs):
        self.labels = labels
        super(LabelLimitLayer, self).__init__(**kwargs)

    def get_config(self):
        config = {'labels': self.labels}
        base_config = super(LabelLimitLayer, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))