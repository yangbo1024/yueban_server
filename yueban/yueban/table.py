# -*- coding:utf-8 -*-

"""
数据表处理: 采用csv格式
每个csv格式为第1行为表头（列名），第2行开始为数据
"""

import json

_all_tables = {}


def get_rows(table_data, index_name, index_value):
    """
    查询所有符合条件的行数据
    :param table_data:
    :param index_name:
    :param index_value:
    :return:
    """
    if not table_data:
        return None
    headers = table_data[0]
    if index_name not in headers:
        return None
    col_idx = headers.index(index_name)
    ret = []
    for row_data in table_data:
        if row_data[col_idx] == index_value:
            row_map = {k:v for k,v in zip(headers, row_data)}
            ret.append(row_map)
    return ret


def get_row(table_data, index_name, index_value):
    """
    查询满足条件的第一行数据
    :param table_data:
    :param index_name:
    :param index_value:
    :return:
    """
    if not table_data:
        return None
    headers = table_data[0]
    if index_name not in headers:
        return None
    col_idx = headers.index(index_name)
    for row_data in table_data:
        if row_data[col_idx] == index_value:
            row_map = {k:v for k,v in zip(headers, row_data)}
            return row_map
    return None


def get_cell(table_data, index_name, index_value, query_column):
    """
    获取一个单元格数据
    :param table_data:
    :param index_name:
    :param index_value:
    :param query_column:
    :return:
    """
    row_map = get_row(table_data, index_name, index_value)
    if not row_map:
        return None
    return row_map.get(query_column)


def get_int(table_data, index_name, index_value, query_column):
    """
    以整数形式返回单元格数据
    :param table_data:
    :param index_name:
    :param index_value:
    :param query_column:
    :return:
    """
    cell = get_cell(table_data, index_name, index_value, query_column)
    return int(cell) if cell else 0


def get_float(table_data, index_name, index_value, query_column):
    cell = get_cell(table_data, index_name, index_value, query_column)
    return float(cell) if cell else 0


def get_string(table_data, index_name, index_value, query_column):
    cell = get_cell(table_data, index_name, index_value, query_column)
    return cell


def get_list(table_data, index_name, index_value, query_column):
    cell = get_cell(table_data, index_name, index_value, query_column)
    return json.loads(cell) if cell else []


def get_dict(table_data, index_name, index_value, query_column):
    cell = get_cell(table_data, index_name, index_value, query_column)
    return json.loads(cell) if cell else {}