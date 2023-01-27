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

from pyfiglet import Figlet

from ctypes import *

from opcodes import opcode_string

class LogOpcode(Structure):
    _pack = 1
    _fields_ = [
        ("opcode", c_uint8)
    ]
    opcode_to_str = {
        0 : "invalid",

    }
    def __str__(self):
        return opcode_to_str[self.opcode]

class FileHash(Structure):
    _pack = 1
    _fields_ = [
        ("file_hash", c_uint8 * 32)
    ]
    def __str__(self):
        return "".join(map(str, self.file_hash))

class LogRecordOpen(Structure):
    _pack = 1
    _fields_ = [
        ("file_hash", FileHash),
        ("file_handle", c_uint64),
        ("file_name", c_char * 64),
        ("flags", c_uint32),
        ("unused", c_uint32),
    ]
    def __str__(self):
        return f"{self.file_hash} {self.file_handle:016x} " + \
               f'{self.file_name.decode()} ' + \
               f"{self.flags:08x} "

class LogRecordRW(Structure):
    _pack = 1
    _fields_ = [
        ("file_hash", FileHash),
        ("file_handle", c_uint64),
        ("offset", c_uint64),
        ("length", c_uint64),
    ]
    def __str__(self):
        return f"{self.file_hash} {self.file_handle:016x} " + \
               f"{self.offset:016x} {self.length:016x}"

class LogRecordGeneric(Structure):
    _pack = 1
    _fields_ = [
        ("file_hash", FileHash),
        ("file_handle", c_uint64),
        ("arg", c_uint64 * 4),
    ]
    def __str__(self):
        return f"{self.file_hash} {self.file_handle:016x}" + \
               f"{self.arg[0]:016x} {self.arg[1]:016x} " + \
               f"{self.arg[2]:016x} {self.arg[3]:016x}"

class LogDataUnion(Union):
    _pack = 1
    _fields_ = [
        ("generic", LogRecordGeneric),
        ("open", LogRecordOpen),
        ("rw", LogRecordRW),
    ]

class LogRecord(Structure):
    _pack = 1
    _fields_ = [
        ("core", c_uint16),
        ("opcode", c_uint8),
        ("unused", c_uint8 * 5),
        ("pid", c_uint32),
        ("tid", c_uint32),
        ("sec", c_uint64),
        ("nsec", c_uint64),
        ("data", LogDataUnion),
    ]
    def time_string(self):
        ts = time.gmtime(self.sec)
        return f"{ts.tm_year:04d}-{ts.tm_mon:02d}-{ts.tm_mday:02d} "\
        f"{ts.tm_hour:02d}:{ts.tm_min:02d}:{ts.tm_sec:02d}.{self.nsec:09d}"

    def __eq__(self, other):
        return self.sec == other.sec and self.nsec == other.nsec

    def __lt__(self, other):
        return self.sec < other.sec or (self.sec == other.sec and self.nsec < other.nsec)

    def __gt__(self, other):
        return self.sec > other.sec or (self.sec == other.sec and self.nsec > other.nsec)

    def __str__(self):
        ts = self.time_string()
        head = f"{ts} {self.core:02d} {self.pid:x} {self.tid:x} {self.opcode} {opcode_string[self.opcode]} "
        data = ""
        if self.opcode == 13: # Open
            data = str(self.data.open)
        elif self.opcode in [14, 15, 32, 33]: # read/write/fallocate/lseek
            data = str(self.data.rw)
        else:
            data = str(self.data.generic)
        return head + data

class LogViewer:
    """Application for viewing logs.."""

    header = "date,time,core,pid,tid,sec,nsec,daarg0,arg1,arg2,arg3,arg4,arg5,arg6,arg7"
    def __init__(self):
        self._args = None

    def get_parser(self, parent_parser=False):
        parser = argparse.ArgumentParser(formatter_class=RawTextHelpFormatter,
                                         description="Application for viewing logs.\n",
                                         add_help=True)
        
        parser.add_argument("--debug", "-D", action="store_true",
                            help="enable debug output")
        parser.add_argument("--merge", default="log_core_",
                            help="merge files.")
        parser.add_argument("--file", "-f", default="log_core_0.bin",
                            help="file name or prefix")
        parser.add_argument("--output", "-o", default="log_merged.txt",
                            help="output file path")
           
        return parser

    def _parse_args(self):
        self._args = self.get_parser().parse_args()
        return True

    @staticmethod
    def _banner():
        print()
        f = Figlet(font='slant')
        print(f.renderText('LogViewer'))

    def trace(self, message):
        if self._args.verbose or self._args.log_level != "OFF":
            print("*" * 50)
            print(message)
            print("*" * 50)
        else:
            print()
            print(message)

    def view_file(self, filename):
        print(f"filename: {filename}")

        buf = LogRecord()

        with open(filename,'rb') as file_object:
            rc = file_object.readinto(buf)
            while rc == sizeof(buf): # Will read sizeof(buf) bytes from file
                print(buf)
                rc = file_object.readinto(buf)

        #print(f"{time_struct}.{buf.nsec}")

    def merge_files(self, files, output_fd):
        file_fds = {}
        total_records = 0
        for file in files:
            core = file.replace(self._args.merge, "").replace(".bin", "")
            file_fds[core] = open(file, "rb")

        if len(file_fds):
            print(LogViewer.header, file=output_fd)
        batch_size = 100000
        records = []
        while len(file_fds) != 0:
            completed_cores = []
            # Read in a batch of each file.
            for core, fd in file_fds.items():
                for i in range(0, batch_size):
                    rec = LogRecord()
                    byte_count = fd.readinto(rec)
                    #print(rec)
                    if byte_count != sizeof(LogRecord):
                        completed_cores.append(core)
                        break
                    else:
                        records.append(rec)
            records.sort()

            # We can guarantee that at least batch size records are sorted.
            # Output these records.
            flush_count = min(len(records), batch_size)
            for i in range(0, flush_count):
                rec_string = ",".join(str(records[i]).split(" "))
                print(rec_string, file=output_fd)
            total_records += flush_count
            print(f"record_count: {total_records}", end='\r')
            del records[0:batch_size]

            for core in completed_cores:
                del file_fds[core]

        # Whatever is left should be printed also
        for rec in records:
            rec_string = ",".join(str(rec).split(" "))
            print(rec_string, file=output_fd)
        total_records += len(records)
        print(f"record_count: {total_records}")

    def merge(self, merge_prefix):
        files = glob.glob(merge_prefix + "*.bin")

        with open(self._args.output, "w") as fd:
            self.merge_files(files, fd)

    def run(self):
        print(sys.argv[0] + " starting")
        
        if not self._parse_args():
            return
        LogViewer._banner()

        if self._args.merge:
            self.merge(self._args.merge)
        elif self._args.file != None:
            self.view_file(self._args.file)


if __name__ == "__main__":
    
    bench = LogViewer()
    bench.run()