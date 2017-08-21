# -*- coding:utf-8 -*-

"""
CSV table handling
for each csv table:
    1st line: column(index) names
    2nd line~end: data rows
"""

import json
from . import config
import os
from . import utility
import traceback
import csv
import os.path


TYPE_FUNC_MAP = {
    'int': lambda x: int(x) if x else 0,
    'long': lambda x: int(x) if x else 0,
    'float': lambda x: float(x) if x else 0,
    'str': lambda x: x,
    'string': lambda x: x,
    'json': json.loads,
    'list': json.loads,
    'dict': json.loads,
}


_cached_mtimes = {}
_cached_tables = {}
_inited = False


def _get_table_path(table_name):
    table_file_name = table_name + '.csv'
    csv_dir = config.get_csv_dir()
    path = os.path.join(csv_dir, table_file_name)
    return path


def _load_table_data(path):
    table_data = []
    with open(path) as f:
        reader = csv.reader(f)
        headers = []
        type_funcs = []
        for i, row in enumerate(reader):
            if i == 0:
                for col in row:
                    tp_begin = col.index('(')
                    tp_end = col.index(')')
                    header = col[:tp_begin]
                    tp_func = col[tp_begin+1:tp_end]
                    headers.append(header)
                    type_funcs.append(tp_func)
            else:
                if not row[0]:
                    break
                row_data = {}
                for j, col in enumerate(row):
                    tpf = type_funcs[j]
                    f = TYPE_FUNC_MAP[tpf]
                    row_data[headers[j]] = f(col)
                table_data.append(row_data)
    return table_data


def _get_newest_table_data(table_name):
    path = _get_table_path(table_name)
    try:
        stat_info = os.stat(path)
        old_time = _cached_mtimes.get(table_name, 0)
        if stat_info.st_mtime > old_time:
            _cached_mtimes[table_name] = stat_info.st_mtime
            # update table data
            table_data = _load_table_data(path)
            _cached_tables[table_name] = table_data
            return table_data
        else:
            table_data = _cached_tables.get(table_name)
            if not table_data:
                # first time load
                table_data = _load_table_data(path)
                _cached_tables[table_name] = table_data
            return table_data
    except Exception as e:
        utility.print_out(e, traceback.format_exc())


def update_table(table_name, table_data_str, encoding='utf-8'):
    path = _get_table_path(table_name)
    with open(path, 'w', encoding=encoding) as f:
        f.write(table_data_str)
    _get_newest_table_data(table_name)


def get_table(table_name):
    """
    Get the whole table data
    :param table_name:
    :return:
    """
    return _get_newest_table_data(table_name)


def get_rows(table_name, index_name, index_value):
    """
    Get all rows by query
    :param table_name:
    :param index_name:
    :param index_value:
    :return:
    """
    table_data = _get_newest_table_data(table_name)
    if not table_data:
        return None
    ret = [row_data for row_data in table_data if row_data[index_name] == index_value]
    return ret


def get_row(table_name, index_name, index_value):
    """
    Get 1 row
    :param table_name:
    :param index_name:
    :param index_value:
    :return:
    """
    table_data = _get_newest_table_data(table_name)
    if not table_data:
        return None
    for row_data in table_data:
        if row_data[index_name] == index_value:
            return row_data
    return None


def get_cell(table_name, index_name, index_value, query_column):
    """
    Get data of a cell(grid)
    :param table_name:
    :param index_name:
    :param index_value:
    :param query_column:
    :return:
    """
    row_map = get_row(table_name, index_name, index_value)
    if not row_map:
        return None
    return row_map.get(query_column)

