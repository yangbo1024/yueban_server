# -*- coding:utf-8 -*-

"""
Log functions
"""

import asyncio
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

