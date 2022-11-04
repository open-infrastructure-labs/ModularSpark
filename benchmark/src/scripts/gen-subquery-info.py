#!/usr/bin/env python3
import json
import argparse
import csv
import os
import subprocess
from argparse import RawTextHelpFormatter
from operator import itemgetter
from pyfiglet import Figlet


class Table:

    def __init__(self, d: dict):
        self.name = d['table name']
        self.path = d['path']
        self.location = d['data center']
        self.bytes = d['bytes']
        self.rows = int(d['metastore rows'])
        self.row_groups = d['metastore row groups']
        self.pq_rows = d['parquet rows']
        self.pq_row_groups = d['parquet row groups']


class Result:
    def __init__(self, d: dict):
        self.name = d['query']
        self.status = d['status']
        self.rows = int(d['rows'])
        self.seconds = float(d['seconds'])


class GenSubqueryInfo:
    """Gathers information on subqueries for a data set and saves the results in a json file.

       The input data is automatically generated if it does not exist including:
        - The table file, (typically tables.csv) which has the sizes of the tables.
        - The qflock_log.txt file, which has the information on all subqueries.
        - The queries.json file, which is generated from the qflock_log, as a unique set of queries
          which is saved as a json file (typically queries.json).

        - Finally we will have a list of queries that is then filtered by the input argument
          of --table_name.
        - For this list of queries, we will run the subquery in Spark to generate the actual number of rows.
        - All of the resulting information is saved in a file, typically
    """
    default_json_path = "../data/queries.json"
    default_json_output_path = "../data/queries_actual.json"
    default_table = "store_sales"
    default_table_path = "../data/tables.csv"
    qflock_log_path = "../data/qflock_log.txt"
    if False:
        gen_tables_cmd = './../get-table-info.py'
        gen_qflock_log_cmd = '../docker-bench.py --query_range "*" --explain --ext remote'
        gen_subqueries_json_cmd = './parse_qflock_query_log.py'
        run_subquery_cmd = './../docker-bench.py '
    else:
        gen_tables_cmd = './get-table-info.sh ../data'
        gen_qflock_log_cmd = '../qflock-bench.py --query_range "*" --explain --ext remote'
        gen_subqueries_json_cmd = './parse_qflock_query_log.py'
        run_subquery_cmd = './../qflock-bench.py '
    default_rows_pct = 0.0001
    subquery_error_vs_estimated = "../data/queries_vs_estimated.csv"

    def __init__(self):
        self._args = None
        self._exit_code = 0
        self._tables = None
        self._subquery_dict = None
        self._subqueries = []
        self._valid_tables = []
        self._subquery_actual_dict = None
        self._set_working_dir()

    def _set_working_dir(self):
        abspath = os.path.abspath(__file__)
        dname = os.path.dirname(abspath)
        # os.chdir(os.path.join(dname, ".."))
        os.chdir(dname)
        print(f"working dir: {os.getcwd()}")

    @staticmethod
    def _get_parser():
        parser = argparse.ArgumentParser(formatter_class=RawTextHelpFormatter,
                                         description="Run a set of subqueries.\n")
        parser.add_argument("--debug", "-dbg", action="store_true",
                            help="enable debugger")
        parser.add_argument("--verbose", "-v", action="store_true",
                            help="Increase verbosity of output.")
        parser.add_argument("--stats", action="store_true",
                            help="Show stats only")
        parser.add_argument("--create_views", action="store_true",
                            help="Create sorted files")
        parser.add_argument("--json_output", default=GenSubqueryInfo.default_json_output_path,
                            help=f"Output file.  Default is {GenSubqueryInfo.default_json_output_path}")
        parser.add_argument("--json_input_path", default=GenSubqueryInfo.default_json_path,
                            help=f"json input file.  Default is {GenSubqueryInfo.default_json_path}")
        parser.add_argument("--table_name", default=GenSubqueryInfo.default_table,
                            help=f"Table to run subqueries for.  Default is {GenSubqueryInfo.default_table}")
        parser.add_argument("--table_file_path", default=GenSubqueryInfo.default_table_path,
                            help=f"Table to run subqueries for.  Default is {GenSubqueryInfo.default_table_path}")
        parser.add_argument("--table_rows_pct", default=GenSubqueryInfo.default_rows_pct,
                            help=f"Max allowable table rows as percentage of total.  ",
                            type=float)
        return parser

    def _parse_args(self):
        self._args = self._get_parser().parse_args()
        return True

    @staticmethod
    def _banner():
        print()
        f = Figlet(font='slant')
        print(f.renderText('GetSubQInfo'))

    @staticmethod
    def _create_tables():
        cmd = f'{GenSubqueryInfo.gen_tables_cmd}'
        rc = subprocess.call(cmd, shell=True)
        if rc != 0:
            print("Failed getting table info")
            exit(1)

    def _calc_valid_tables(self):
        """Determines which tables we should consider, and drops those which are too small.

            The criteria we use uses a dynamic threshold of the percentage of the overall size.
        """
        total_rows = 0

        for t in self._tables:
            total_rows += self._tables[t].rows

        for t in self._tables.values():
            pct = t.rows / total_rows
            if pct >= self._args.table_rows_pct:
                self._valid_tables.append(t.name)
            # else:
            #     print(f"{t.name} {str(t.rows)} {pct}")

    def _load_tables(self):
        if not os.path.exists(self._args.table_file_path):
            print(f"{self._args.table_file_path} does not exist, generating.")
            self._create_tables()
        tables = dict()
        with open(self._args.table_file_path, newline='') as csv_file:
            reader = csv.DictReader(csv_file, delimiter=',')
            for row in reader:
                t = Table(row)
                tables[t.name] = t
        self._tables = tables

        self._calc_valid_tables()
        print(f"valid tables: {self._valid_tables}")

    @staticmethod
    def _create_subqueries_json():
        cmd = f'{GenSubqueryInfo.gen_subqueries_json_cmd}'
        rc = subprocess.call(cmd, shell=True)
        if rc != 0:
            print("Failed generating subqueries json")
            exit(1)

    @staticmethod
    def _create_qflock_log():
        cmd = f'{GenSubqueryInfo.gen_qflock_log_cmd}'
        rc = subprocess.call(cmd, shell=True)
        if rc != 0:
            print("Failed generating subqueries json")
            exit(1)

    def _load_subqueries(self):
        if not os.path.exists(self._args.json_input_path):
            if not os.path.exists(GenSubqueryInfo.qflock_log_path):
                print(f"{GenSubqueryInfo.qflock_log_path} does not exist, generating.")
                self._create_qflock_log()
            print(f"{self._args.json_input_path} does not exist, generating.")
            self._create_subqueries_json()
        with open(self._args.json_input_path, 'r') as fd:
            self._subquery_dict = json.load(fd)

    def _get_subqueries(self):
        self._load_subqueries()
        for subquery in self._subquery_dict['subqueries']:
            t = subquery['table']
            subquery['table_key'] = t
            subquery['table_rows'] = int(self._tables[t].rows)
            self._subqueries.append(subquery)

        # We will sort all the subqueries by both number of rows and the table name.
        self._subqueries = sorted(self._subqueries, key=itemgetter('table_rows', 'table_key'), reverse=True)

        # Only use entries which have filters.
        self._subqueries = [sq for sq in self._subqueries if sq['unique_filters'] != ""]

        if self._args.table_name != "*":
            valid_tables = self._args.table_name.split(",")
            # Choose queries that are from our list of selected tables.
            self._subqueries = [sq for sq in self._subqueries if sq['table_key'] in valid_tables]
        else:
            # Choose queries that are within the correct size threshold.
            self._subqueries = [sq for sq in self._subqueries if sq['table_key'] in self._valid_tables]

    @staticmethod
    def _load_results(file_name: str):
        results = dict()
        with open(file_name, newline='') as csv_file:
            reader = csv.DictReader(csv_file, delimiter=',')
            for row in reader:
                if row['status'] == 'PASSED':
                    r = Result(row)
                    results[r.name] = r
        return results

    def _run_subquery(self, subquery):
        results_file = 'subquery.csv'
        results_path = os.path.join("../", results_file)

        if True:
            if os.path.exists(results_path):
                os.remove(results_path)
            q = subquery['query']
            cmd = f'{GenSubqueryInfo.run_subquery_cmd} '\
                  f'--query_text \"{q}\" --results_path ./ --results_file {results_file}'
            rc = subprocess.call(cmd, shell=True,
                                 stdout=subprocess.DEVNULL,
                                 stderr=subprocess.STDOUT)
            if rc != 0:
                # Zero rows.
                return 0
        results = self._load_results(results_path)
        return results['custom query'].rows

    def _run_subqueries(self):

        if not self._args.stats:
            i = 0
            print(f"running {len(self._subqueries)} queries")
            for sq in self._subqueries:
                rows = self._run_subquery(sq)
                print(f"query {i} actual_rows {rows} estimated_rows {sq['estimated_rows']} query {sq['query']}")
                sq['actual_rows'] = int(rows)
                i += 1
        else:
            i = 0
            print(f"running {len(self._subqueries)} queries")
            for sq in self._subqueries:
                print(f"query {i} estimated rows {sq['estimated_rows']} query {sq['query']}")
                i += 1

    def _calc_stats(self):
        """Calculates statistics related to accuracy of Spark estimates"""
        for sq in self._subqueries:
            if 'actual_rows' in sq:
                sq['rows_diff'] = abs(sq['actual_rows'] - sq['estimated_rows'])
                if sq['estimated_rows'] != 0:
                    sq['error_vs_estimated'] = sq['rows_diff'] / sq['estimated_rows']
                else:
                    sq['error_vs_estimated'] = 0
                sq['error_vs_overall'] = sq['rows_diff'] / sq['table_rows']

    def _save_json(self):
        json_data = json.dumps(self._subqueries, indent=4, sort_keys=True)
        with open(self._args.json_output, 'w') as fd:
            fd.write(json_data)

    def _view_subqueries(self):
        estimated = sorted(self._subquery_actual_dict, key=itemgetter('error_vs_estimated'), reverse=True)
        with open(GenSubqueryInfo.subquery_error_vs_estimated, "w") as fd:
            header = "table,actual_rows,estimated_rows,table_rows,error_vs_estimated,error_vs_overall,"\
                     "query"
            fd.write(f"{header}\n")
            for sq in estimated:
                row = f"{sq['table']},{sq['actual_rows']},{sq['estimated_rows']},"\
                      f"{sq['table_rows']},{sq['error_vs_estimated']},{sq['error_vs_overall']},"\
                      f"{sq['query']}"
                fd.write(f"{row}\n")

    def _load_subqueries_actual(self):
        if not os.path.exists(GenSubqueryInfo.default_json_output_path):
            print(f"{GenSubqueryInfo.default_json_output_path} does not exist")
            exit(1)
        with open(GenSubqueryInfo.default_json_output_path, 'r') as fd:
            self._subquery_actual_dict = json.load(fd)

    def run(self):
        """Generates and Returns the subquery information.

            The main information that is generated is the:
            1) Subquery Spark estimated rows
            2) Subquery Spark actual rows.
            3) Stats related to accuracy
        """
        self._banner()
        self._parse_args()
        if self._args.create_views:
            self._load_subqueries_actual()
            self._view_subqueries()
        else:
            self._load_tables()
            self._load_subqueries()
            self._get_subqueries()
            self._run_subqueries()
            if not self._args.stats:
                self._calc_stats()
            self._save_json()


if __name__ == "__main__":
    run_subquery = GenSubqueryInfo()
    run_subquery.run()
