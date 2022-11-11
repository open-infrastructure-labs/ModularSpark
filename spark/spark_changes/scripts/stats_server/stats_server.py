#!/usr/bin/python3 -u
import threading
import os
import sys
import importlib.util
import argparse
import json
import numpy as np
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


def load_stats_module():
    """returns the module object for a dynamically loaded stats module."""
    if 'STATS_SERVER_FUNC' in os.environ:
        module_fullpath = os.environ['STATS_SERVER_FUNC']
    else:
        module_fullpath = os.path.abspath("stats_calc.py")
    spec = importlib.util.spec_from_file_location("calc_stats", module_fullpath)
    stats_module = importlib.util.module_from_spec(spec)
    sys.modules["calc_stats"] = stats_module
    spec.loader.exec_module(stats_module)
    return stats_module


_stats_module = load_stats_module()
_stats_object = _stats_module.get_stats_object()
logging_lock = threading.Lock()


class StatsRequestHandler(http.server.BaseHTTPRequestHandler):
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

    @staticmethod
    def _get_percentage(request):
        return _stats_object.get_filter_percentage(request['table'], request['filter'])

    def do_POST(self):
        self.log(f'POST {self.path}')
        self.parse_url()
        if hasattr(self, "op") and self.op == 'GET_TABLES':
            return self._get_tables()
        else:
            return self._get_stats()

    def _get_stats(self):
        json_request = self.headers['request-json']
        request = json.loads(json_request)
        self.log(f'request {request}')
        self.send_response(HTTPStatus.OK)
        self.send_header('Transfer-Encoding', 'chunked')
        self.end_headers()

        # Get an estimate of the percentage of rows to be returned by this filter
        # for this table.
        percentage = self._get_percentage(request)
        print(f"table: {request['table']} filter: {request['filter']} percentage: {percentage}")

        # Send back the percentage calculated.
        data = np.array([percentage])
        data_buffer = data.byteswap().newbyteorder().tobytes()
        writer = ChunkedWriter(self.wfile)
        writer.write(data_buffer)
        writer.close()
        self.wfile.flush()

    def _get_tables(self):
        self.send_response(HTTPStatus.OK)
        self.send_header('Transfer-Encoding', 'chunked')
        self.end_headers()

        writer = ChunkedWriter(self.wfile)
        tables = _stats_object.get_valid_tables()
        if tables.dtype != 'object' or not isinstance(tables[0], str):
            raise Exception("unknown type for tables, expected numpy array of strings")
        s = tables.astype(dtype=np.bytes_)
        data_buffer = s.tobytes()
        # The header consists of the
        # 1) size of each string
        # 2) the total length of the data.
        header = np.array([s.dtype.itemsize, len(data_buffer)], np.int32)
        writer.write(header.byteswap().newbyteorder().tobytes())
        writer.write(data_buffer)
        writer.close()
        self.wfile.flush()


class StatsServer(http.server.ThreadingHTTPServer):
    def __init__(self, server_address, handler, config):
        super().__init__(server_address, handler)
        self.config = config


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Stats Server.')
    parser.add_argument('-i', '--ip', default='', help='server ip address')
    parser.add_argument('-p', '--port', type=int, default='9860', help='Server port')
    parser.add_argument('-v', '--verbose', type=int, default='0', help='Verbose mode')
    args = parser.parse_args()
    print(f'Listening to port:{args.port} ip:{args.ip}')
    stats_server = StatsServer((args.ip, args.port), StatsRequestHandler, args)
    try:
        stats_server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        # Clean-up server (close socket, etc.)
        stats_server.server_close()
