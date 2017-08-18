# -*- coding:utf-8 -*-

"""
Log functions
"""

import asyncio
from . import storage
from datetime import datetime
from . import config


_log_collection = None


async def _log(category, log_type, *args):
    """
    Log to a single file named category with python logging
    :param args:
    :return:
    """
    global _log_collection
    if not args:
        return
    arg_list = [str(arg) for arg in args]
    arg_list.insert(0, log_type)
    s = " ".join(arg_list)
    doc = {
        'time': datetime.now(),
        'category': category,
        'log': s,
    }
    await _log_collection.insert(doc)


async def info(category, *args):
    await _log(category, 'INFO', *args)


def info_async(category, *args):
    asyncio.ensure_future(info(category, *args))


async def warning(category, *args):
    await _log(category, 'WARNING', *args)


def warning_async(category, *args):
    asyncio.ensure_future(warning(category, *args))


async def error(category, *args):
    await _log(category, 'ERROR', *args)


def error_async(category, *args):
    asyncio.ensure_future(error(category, *args))


async def ensure_collection():
    """
    Only call once in whole system's lifetime
    :return:
    """
    db = storage.get_stat_conn()
    col_name = config.get_log_collection()
    col = db[col_name]
    indexes = [
        ('time', 1),
        ('category', 1),
    ]
    expire_seconds = config.get_log_expire_seconds()
    expire_seconds = int(expire_seconds)
    await col.create_index(indexes, expireAfterSeconds=expire_seconds)


async def initialize():
    global _log_collection
    db = storage.get_stat_conn()
    if not db:
        raise RuntimeError("you should init stat-mongodb before log")
    col_name = config.get_log_collection()
    _log_collection = db[col_name]
