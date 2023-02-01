#!/usr/bin/env python3
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

import fio


if __name__ == "__main__":

    t1 = fio.FioFileTest()
    t1.run({"bs": "8k", "readwrite": "read", "size": "10m"})
    t1.run({"bs": "8k", "readwrite": "write", "size": "10m"})

    scaling_args = {"io_submit_mode": "offload"}
    t2 = fio.FioFileTest(scaling_args)
    for i in [1, 2, 4, 8, 16, 32, 64]:
        t2.run({"bs": "8k", "readwrite": "read", "size": "2g", "iodepth": i, "nrfiles": i})

    for i in [1, 2, 4, 8, 16, 32, 64]:
        t2.run({"bs": "128k", "readwrite": "write", "size": "2g", "iodepth": i, "nrfiles": i})

    t1.save_results()
    t2.save_results()
