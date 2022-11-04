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
import sys
import os
import time
import subprocess
import argparse
from argparse import RawTextHelpFormatter
from pyfiglet import Figlet

copy_files = [
    {'file': "src/main/scala/org/apache/spark/sql/catalyst/parser/AstBuilder.scala",
     'dest_root': "sql/catalyst/" },
    {'file': "src/main/scala/org/apache/spark/sql/catalyst/plans/logical/basicLogicalOperators.scala",
     'dest_root': "sql/catalyst/" },
    {'file': "src/main/scala/org/apache/spark/sql/catalyst/trees/TreePatterns.scala",
     'dest_root': "sql/catalyst/" },
    {'file': "src/main/scala/org/apache/spark/sql/execution/SparkStrategies.scala",
     'dest_root': "sql/core/" },
]
class CopySource:
    """
    Copy the source files from our spark_changes to spark folder.
    """
    log_dir = "logs"

    def __init__(self):
        self._args = None
        self._exit_code = 0

    def _get_parser(self):
        parser = argparse.ArgumentParser(formatter_class=RawTextHelpFormatter,
                                         description="Copy sources from spark_changes to spark.\n")
        parser.add_argument("--debug", "-dbg", action="store_true",
                            help="enable debugger")
        parser.add_argument("--verbose", "-v", action="store_true",
                            help="Increase verbosity of output.")
        parser.add_argument("--src", default="../",
                            help="Source to copy from")
        parser.add_argument("--dest", default="../../spark",
                            help="Dest to copy to")
        return parser

    def _parse_args(self):
        self._args = self._get_parser().parse_args()
        return True

    @staticmethod
    def _banner():
        print()
        f = Figlet(font='slant')
        print(f.renderText('CopySource'))

    def copy_file(self, file_entry):
        source = os.path.join(self._args.src, file_entry['file'])
        dest = os.path.join(self._args.dest, file_entry['dest_root'])
        dest = os.path.join(dest, file_entry['file'])
        if not os.path.exists(source):
            print(f"source does not exist: {source}")
        elif not os.path.exists(dest):
            print(f"dest does not exist: {dest}")
        else:
            cmd = f"cp {source} {dest}"
            print(cmd)
            rc = subprocess.call(cmd, shell=True)
            if rc != 0:
                print(f"failed cmd: {cmd}")
            return rc

    def copy_source(self):
        for file_entry in copy_files:
            self.copy_file(file_entry)


    def run(self):
        if not self._parse_args():
            return
        self.copy_source()
        exit(self._exit_code)


if __name__ == "__main__":
    app = CopySource()
    app.run()
