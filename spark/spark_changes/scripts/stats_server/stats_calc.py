#!/usr/bin/python3 -u
import threading
import os
import sys
import numpy as np
import json

# This is an example module which contains a get_filter_percentage() method.

class BasicStatsObject:

    default_json_stats = "stats.json"

    def __init__(self):
        with open(BasicStatsObject.default_json_stats, 'r') as fd:
            self._stats_table = json.load(fd)['tables']
            self._tables = self._stats_table.keys()

    def get_filter_percentage(self, table, query):
        """Fetches a percentage of rows to return.

           This is a fixed percentage, as a demonstration of what we could do."""
        if "WHERE " in query:
            query_substr = query.split("WHERE ")[1].strip()
        else:
            query_substr = ""
        print(f"query: {query_substr}")
        if table in self._tables:
            for item in self._stats_table[table]["queries"]:
                print(f'[{query_substr}] [{item["query"]}] {item["query"] == query_substr}')
            found_query = next((item for item in self._stats_table[table]["queries"] \
                                if item["query"] == query_substr), None)
            if found_query is not None:
                return found_query["percent"]
            else:
                return self._stats_table[table]["default_percent"]
        else:
            return 0.42

    def get_valid_tables(self):
        """returns the list of tables that this module can calc stats for."""
        keys = list(self._stats_table.keys())
        tables = np.empty(len(keys), dtype='object')
        i = 0
        for k in keys:
            tables[i] = k
            i += 1
        return tables

def get_stats_object():
    return BasicStatsObject()
