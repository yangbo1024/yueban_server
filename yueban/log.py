# -*- coding:utf-8 -*-

"""
Log functions
"""

from . import communicate


async def _log(category, log_type, *args):
    """
    Log to a single file named category with python logging
    :param args:
    :return:
    """
    if not args:
        return
    arg_list = [str(arg) for arg in args]
    arg_list.insert(0, log_type)
    s = " ".join(arg_list)
    await communicate.post_logger('/yueban/log', [category, s])


async def info(category, *args):
    await _log(category, 'INFO', *args)


async def warning(category, *args):
    await _log(category, 'WARNING', *args)


async def error(category, *args):
    await _log(category, 'ERROR', *args)


async def stat(collection_name, documents):
    """
    Stats to MongoDB
    :param collection_name:
    :param documents:
    :return:
    """
    await communicate.post_logger('/yueban/stat', [collection_name, documents])
