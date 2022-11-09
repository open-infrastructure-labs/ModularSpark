#!/usr/bin/python3 -u
import threading
import time
import gc
import argparse
import json
import struct
import numpy
import http.server
import http.client
from http import HTTPStatus
import urllib.parse


class ChunkedWriter:
    def __init__(self, wfile):
        self.wfile = wfile

    def write(self, data):
        self.wfile.write(f'{len(data):x}\r\n'.encode())
        self.wfile.write(data)
        self.wfile.write('\r\n'.encode())

    def close(self):
        self.wfile.write('0\r\n\r\n'.encode())


logging_lock = threading.Lock()


class FuncRequestHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def log(self, msg):
        if self.server.config.verbose:
            logging_lock.acquire()
            print(msg)
            logging_lock.release()

    def parse_url(self):
        url = urllib.parse.urlparse(self.path)
        for q in url.query.split('&'):
            if 'user.name=' in q:
                user = q.split('user.name=')[1]
                setattr(self, 'user', user)
            if 'op=' in q:
                op = q.split('op=')[1]
                setattr(self, 'op', op)

    def do_POST(self):
        self.log(f'POST {self.path}')
        self.parse_url()
        # data = self.rfile.read(int(self.headers['Content-Length']))
        json_request = self.headers['request-json']
        config = json.loads(json_request)
        self.log(f'config {config}')
        self.send_response(HTTPStatus.OK)
        self.send_header('Transfer-Encoding', 'chunked')
        self.end_headers()

        self.read_data()

        # For now just echo back the data we received.
        writer = ChunkedWriter(self.wfile)
        writer.write(data)
        writer.close()
        self.wfile.flush()

    def read_data(self):
        # Read the magic and length
        header = self.rfile.read(4)
        magic = struct.unpack("!i", header)
        print(f"magic {magic}")
        header = self.rfile.read(4)
        magic = struct.unpack("!i", header)
        print(f"magic {magic}")
        header = self.rfile.read(4)
        length = struct.unpack("!i", header)
        print(f"length {length}")
        data_types = []
        for i in range(0, length):
            header = self.rfile.read(4)
            data_types[i] = struct.unpack("!i", header)
        print(f"data_types: " + data_types)
        print()

    def do_GET(self):
        self.log(f'GET {self.path}')
        self.parse_url()

        if self.op == 'FUNCTION':
            return self.call_function()

    def call_function(self):
        data = self.get_data()
        self.send_response(HTTPStatus.OK)
        self.send_header('Transfer-Encoding', 'chunked')
        self.end_headers()

        writer = ChunkedWriter(self.wfile)

        writer.close()




class FunctionServer(http.server.ThreadingHTTPServer):
    def __init__(self, server_address, handler, config):
        super().__init__(server_address, handler)
        self.config = config


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run Function server.')
    parser.add_argument('-i', '--ip', default='10.124.48.63', help='http-address')
    parser.add_argument('-p', '--port', type=int, default='9860', help='Server port')
    parser.add_argument('-v', '--verbose', type=int, default='0', help='Verbose mode')
    config = parser.parse_args()
    print(f'Listening to port:{config.port} ip:{config.ip}')
    func_server = FunctionServer((config.ip, config.port), FuncRequestHandler, config)
    try:
        func_server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        # Clean-up server (close socket, etc.)
        func_server.server_close()