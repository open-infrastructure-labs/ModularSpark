#!/usr/bin/python3 -u
import threading
import os
import sys
import numpy as np

# This is an example module which contains a get_filter_percentage() method.

class BasicStatsObject:

    def __init__(self):
        self._valid_tables = \
          {'call_center': 0.20, 'inventory': 0.10, 'store_sales': 0.30, 'store': 1.0}

    def get_filter_percentage(self, table, filters):
        """Fetches a percentage of rows to return.

           This is a fixed percentage, as a demonstration of what we could do."""
        if table in self._valid_tables:
            return self._valid_tables[table]
        else:
            return 0.42

    def get_valid_tables(self):
        """returns the list of tables that this module can calc stats for."""
        keys = list(self._valid_tables.keys())
        tables = np.empty(len(keys), dtype='object')
        i = 0
        for k in keys:
            tables[i] = k
            i += 1
        return tables

def get_stats_object():
    return BasicStatsObject()
