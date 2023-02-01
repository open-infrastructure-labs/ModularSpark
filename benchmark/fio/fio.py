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
import argparse
from argparse import RawTextHelpFormatter
sys.path.append("../src/")
from benchmark.command import shell_cmd

class FioResult:
    def __init__(self, output, fio_args, err):
        self._fio_args = fio_args
        io, bw = self.parse_result(output)
        result = {"iops": io, "bw": bw,
                  "bs": fio_args['bs'],
                  "iodepth": fio_args['iodepth'] if 'iodepth' in fio_args else "1",
                  "readwrite": fio_args['readwrite'],
                  "error": err}
        self._result = result

    def parse_result(self, output):
        iops, bw = "", ""
        for line in output:
            if ": IOPS=" in line:
                items = line.lstrip().split(" ")
                iops = items[1].replace(",", "").split("=")[1]
                bw = items[2].replace(",", "").split("=")[1]
        return iops, bw

    def __str__(self):
        r = self._result
        return f"{r['iodepth']},{r['bs']},{r['readwrite']},{r['iops']},{r['bw']}"

class FioTest:
    header = "threads,I/O size,I/O type,iops,MB/s"
    def __init__(self, fio_args={}):
        self._fio_args = fio_args
        self._results = []
        self._args = self.get_parser().parse_args()
        self._fio_args['directory'] = self._args.dir
        self._test_count = 0

    def get_parser(self, parent_parser=False):
        parser = argparse.ArgumentParser(formatter_class=RawTextHelpFormatter,
                                         description="App for running FIO Tests.\n",
                                         add_help=True)

        parser.add_argument("--debug", "-D", action="store_true",
                            help="enable debug output")
        parser.add_argument("--verbose", "-v", action="store_true",
                            help="enable verbose output")
        parser.add_argument("--dir", "-d", default="./",
                            help="root directory to mount for fio")
        parser.add_argument("--results", "-r", default="results.csv",
                            help="results file path")
        return parser

    def get_fio_cmd(self, fio_args={}):
        cmd = "fio "
        for arg, value in fio_args.items():
            cmd += f"--{arg}={value} "
        return cmd


    def run(self, extra_args):
        args = extra_args.copy()
        args.update(self._fio_args)
        cmd = self.get_fio_cmd(args)
        if self._args.verbose:
            print(f"command is: {cmd}")
        err, output = shell_cmd(cmd, enable_stdout=self._args.verbose)
        result = FioResult(output, args, err)
        self._results.append(result)
        if self._test_count == 0:
            print(FioTest.header)
        print(result)
        self._test_count += 1

    def save_results(self):
        with open(self._args.results, "w") as fd:
            print(FioTest.header, file=fd)
            for res in self._results:
                result = str(res)
                print(result, file=fd)


class FileFioTest(FioTest):

    def __init__(self, extra_args={}):
        defaults = {
            "time_based": "1",
            "runtime": "1s",
            "randrepeat": "1",
            "ioengine": "libaio",
            "direct": "0",
            "gtod_reduce": "1",
            "name": "test",
        }
        self._fio_args = defaults
        self._fio_args.update(extra_args)
        super().__init__(self._fio_args)


class FioFileTest(FioTest):

    def __init__(self, extra_args={}):
        defaults = {
            "time_based": "1",
            "runtime": "1s",
            "randrepeat": "1",
            "ioengine": "libaio",
            "direct": "0",
            "gtod_reduce": "1",
            "name": "test",
        }
        self._fio_args = defaults
        self._fio_args.update(extra_args)
        super().__init__(self._fio_args)


