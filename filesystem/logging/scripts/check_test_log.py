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
import os
import time
import sys
import argparse
from argparse import RawTextHelpFormatter
import logging
import glob

class CheckTestLog:

    def __init__(self, file):
        self._filename = file

    def check_file(self):
        with open(self._filename, 'r') as fd:
            header = fd.readline()
            print(f"header: {header}")
            thread_seq_num = {}
            for line in fd.readlines():
                items = line.split(" ")
                core = items[2]
                test_thread = items[5]
                seq = int(items[6], 16)
                if test_thread not in thread_seq_num:
                    thread_seq_num[test_thread] = 0
                if seq != thread_seq_num[test_thread]:
                    print(f"mismatch test thread {test_thread} found {seq} != " + \
                          f"expected {thread_seq_num[test_thread]}")
                thread_seq_num[test_thread] += 1

    def run(self):
        self.check_file()
if __name__ == "__main__":
    t = CheckTestLog("log_merged.txt")

    t.run()