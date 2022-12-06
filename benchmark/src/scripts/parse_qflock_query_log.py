#!/usr/bin/env python3
import sys
import re
import json
import argparse
from argparse import RawTextHelpFormatter
from pyfiglet import Figlet

class ParseQflockLog:
    default_file_path = "../data/qflock_log.txt"
    default_json_path = "../data/queries.json"
    def __init__(self):
        self._file = None
        self.log = {}
        self.stats = {}
        self.log_by_test = {}
        self._args = None
        self._exit_code = 0

    def _get_parser(self):
        parser = argparse.ArgumentParser(formatter_class=RawTextHelpFormatter,
                                         description="Copy sources from spark_changes to spark.\n")
        parser.add_argument("--debug", "-dbg", action="store_true",
                            help="enable debugger")
        parser.add_argument("--verbose", "-v", action="store_true",
                            help="Increase verbosity of output.")
        parser.add_argument("--file", default=ParseQflockLog.default_file_path,
                            help=f"file to parse.  Default is {ParseQflockLog.default_file_path}")
        parser.add_argument("--json", default=ParseQflockLog.default_json_path,
                            help=f"json output file.  Default is {ParseQflockLog.default_json_path}")
        return parser

    def _parse_args(self):
        self._args = self._get_parser().parse_args()
        return True

    @staticmethod
    def _banner():
        print()
        f = Figlet(font='slant')
        print(f.renderText('ParseQueryLog'))

    def get_log_by_test(self):
        for query, log in self.log.items():
            if log['name'] in self.log_by_test:
                print(f"get_log_by_test: duplicate test name {log['name']}, dropping")
            else:
                self.log_by_test[log['name']] = log

    def unique_filters(self, filter_string):
        filters = filter_string.split(",")
        new_filters = []
        for f in filters:
            new_filt0 = re.sub("(\w+ IS NOT NULL)", "", f).strip()
            new_filt = re.sub("(\w+ IS NULL)", "", new_filt0).strip()
            if new_filt != "":
                new_filters.append(new_filt)
        return list(set(new_filters))

    def parse_log(self):
        self.log = {}
        self.stats['total_queries'] = 0
        self.unique_queries = {}
        self.queries = {}
        with open(self._args.file, 'r') as fd:
            for line in fd.readlines():
                if "QueryData" in line:
                    self.stats['total_queries'] += 1
                    items = line.split(" ")
                    name = items[1].split(":")[1].replace(".sql", "").strip()
                    rule_log = items[2].split(":")[1]
                    est_rows = items[3].split(":")[1]
                    query = " ".join(items[4:]).split(":")[1].rsplit("\n")[0].strip()
                    if "WHERE" in query:
                        regex = re.search("SELECT (.+) FROM (.+) WHERE (.+)", query)
                        columns = ",".join(list(map(str.strip, sorted(regex.group(1).split(",")))))
                        table = regex.group(2).strip()
                        filters = ",".join(list(map(str.strip, regex.group(3).split("AND"))))
                        unique_filters = self.unique_filters(filters)
                        query_key = f"{table}_{'_'.join(unique_filters)}"
                    else:
                        regex = re.search("SELECT (.+) FROM (.+)", query)
                        columns = ",".join(list(map(str.strip, sorted(regex.group(1).split(",")))))
                        table = regex.group(2).strip()
                        filters = ""
                        unique_filters = []
                        query_key = f"{table}"
                    has_filters = len(unique_filters) > 0
                    if name not in self.log:
                        query_result = {'name': name,
                                        'queries': {},
                                        'bytes': 0}
                        self.log[name] = query_result
                    else:
                        query_result = self.log[name]
                    if query_key not in self.queries:
                        self.queries[query_key] = {
                        'query': query, 'rule_log': rule_log, 'table': table,
                        'columns': [], 'filters': filters, 'unique_filters': ','.join(unique_filters),
                        'estimated_rows': int(est_rows), 'query_repeat_count': 1, 'query_key': query_key,
                        'tests': [name]}
                    else:
                        self.queries[query_key]['query_repeat_count'] += 1
                        if name not in self.queries[query_key]['tests']:
                            self.queries[query_key]['tests'].append(name)
                    if columns not in self.queries[query_key]['columns']:
                        self.queries[query_key]['columns'].append(columns)
                    if query not in query_result['queries']:
                        query_result['queries'][query] = {
                        'query': query, 'rule_log': rule_log, 'table': table,
                        'columns': columns, 'filters': filters, 'unique_filters': ','.join(unique_filters),
                        'estimated_rows': int(est_rows), 'query_repeat_count': 1, 'query_key': query_key,
                        'test': [name]}
                    else:
                        query_result['queries'][query]['query_repeat_count'] += 1
                    if query not in self.unique_queries:
                        self.unique_queries[query] = 0
                    else:
                        self.unique_queries[query] += 1

        self.stats['unique_queries'] = len(self.unique_queries)
        self.stats['unique_filter_table'] = len(self.queries)

    def show(self):
        # for k, v in self.log.items():
        #     print(f"query name: {k} subqueries: {len(v['queries'].keys())} ")
        #     for query, q_value in v['queries'].items():
        #         print(f" table: {q_value['table']} " +
        #               f" columns: {q_value['columns']} " +
        #               f" filters: {q_value['filters']} " +
        #               f"query: {query}")

        # for k, v in self.queries.items():
        #     cols = list(set(v['columns']))
            # if len(cols) > 1:
            #     print(f"query key: {k} columns: {cols} ")
        print(f" total queries: {self.stats['total_queries']}")
        print(f" total unique queries : {self.stats['unique_queries']}")
        print(f" total unique queries (filter + table): {self.stats['unique_filter_table']}")

    def gen_json(self):
        """Convert the data to json and save as output file."""
        json_dict = {'tests': [],
                     'stats': {}}
        # for k, v in self.log.items():
        #     test = {'name': k, 'subqueries': []}
        #
        #     # print(f"query name: {k} subqueries: {len(v['queries'].keys())} ")
        #     for query, q_value in v['queries'].items():
        #         test['subqueries'].append({'tables': q_value['table'].split(","),
        #                                    'columns': q_value['columns'].split(","),
        #                                    'filters': q_value['filters'].split(","),
        #                                    'estimated_rows': int(q_value['estimated_rows']),
        #                                    'query': query})
        #     json_dict['tests'].append(test)
        for k, v in self.stats.items():
            json_dict['stats'][k] = v
        json_dict['subqueries'] = []
        for k, v in self.queries.items():
            json_dict['subqueries'].append(v)
        json_data = json.dumps(json_dict, indent=4, sort_keys=True)
        # print(json_data)
        with open(self._args.json, 'w') as fd:
            fd.write(json_data)

    def run(self):
        self._banner()
        self._parse_args()
        self.parse_log()
        self.get_log_by_test()
        self.show()
        self.gen_json()

if __name__ == "__main__":
    parse_log = ParseQflockLog()
    parse_log.run()
