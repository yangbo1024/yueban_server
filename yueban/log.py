# -*- coding:utf-8 -*-

"""
Log functions
"""

import datetime
from . import communicate


def debug(*args):
    """
    Only print to std(err)
    :param args:
    :return:
    """
    s = " ".join([str(arg) for arg in args])
    now = datetime.datetime.now()
    time_str = now.strftime('%Y-%m-%d %H:%M:%S,%f')
    print(time_str, s)


async def log(category, *args):
    """
    Log to a single file use logging
    :param args:
    :return:
    """
    if not args:
        return
    arg_list = [str(arg) for arg in args]
    arg_list.insert(0, category)
    s = " ".join(arg_list)
    await communicate.post_logger('log', s)


async def stat(collection_name, documents):
    """
    Stats to MongoDB
    :param collection_name:
    :param documents:
    :return:
    """
    await communicate.post_logger('stat', [collection_name, documents])
