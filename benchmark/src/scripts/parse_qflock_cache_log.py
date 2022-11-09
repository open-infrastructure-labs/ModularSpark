#!/usr/bin/env python3
import sys

class ParseQflockCacheLog:

    def __init__(self, qflock_log):
        self._file = qflock_log
        self.log = {}
        self.parse_log()
        self.log_by_test = {}
        self.get_log_by_test()

    def get_log_by_test(self):
        for query, log in self.log.items():
            if log['name'] in self.log_by_test:
                print(f"get_log_by_test: duplicate test name {log['name']}, dropping")
            else:
                self.log_by_test[log['name']] = log

    def parse_log(self):
        self.log = {}
        with open(self._file, 'r') as fd:
            for line in fd.readlines():
                if "QflockQueryCache:logPotentialHits" in line:
                    items = line.split(" ")
                    name = items[1].split(":")[1].replace(".sql", "")
                    hits = items[2].split(":")[1]
                    query = " ".join(items[3:]).split(":")[1].rsplit("\n")[0]
                    if name not in self.log:
                        query_result = {'name': name,
                                        'hits': 0,
                                 'queries': {}}
                        self.log[name] = query_result
                    if query not in query_result['queries']:
                        query_result['queries'][query] = {'hits': hits}
                    query_result['hits'] += int(hits)
    def show(self):
        total_hits = 0
        for k, v in self.log.items():
            total_hits += int(v['hits'])
            print(f"query name: {k} hits: {v['hits']} subqueries: {len(v['queries'].keys())} ")
            for query, query_values in v['queries'].items():
                print(f"  - {query_values['hits']} - {query}")
        print(f"Number of tests: {len(self.log.items())}")
        print(f"Total hits: {total_hits}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        cr = ParseQflockCacheLog(sys.argv[1])
    else:
        cr = ParseQflockCacheLog("data/qflock_log.txt")
    cr.show()
