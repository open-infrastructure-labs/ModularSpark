#!/usr/bin/env python3
import sys

class ParseQflockLog:

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
                if "QueryData" in line:
                    items = line.split(" ")
                    name = items[1].split(":")[1].replace(".sql", "")
                    rule_log = items[2].split(":")[1]
                    query = " ".join(items[3:]).split(":")[1].rsplit("\n")[0]
                    table = re.search("FROM (.+) WHERE", query).group(1)
                    if name not in self.log:
                        query_result = {'name': name,
                                        'queries': {},
                                        'bytes': 0}
                        self.log[name] = query_result
                    else:
                        query_result = self.log[name]
                    if query not in query_result['queries']:
                        query_result['queries'][query] = {'parts': [],
                        'query': query, 'rule_log': rule_log, 'table': table}

    def show(self):

        for k, v in self.log.items():
            print(f"query name: {k} subqueries: {len(v['queries'].keys())} ")
            for query, q_value  in v['queries'].items():
                print(f" table: {query['table']} " +
                      f"query: {query['query']}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        cr = ParseQflockLog(sys.argv[1])
    else:
        cr = ParseQflockLog("data/qflock_log.txt")
    cr.show()
