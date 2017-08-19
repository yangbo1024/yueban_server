# -*- coding:utf-8 -*-

"""
Log functions
"""

from . import utility


async def _log(category, log_type, *args):
    """
    Log to a single file named category with python logging
    :param args:
    :return:
    """
    if not args:
        return
    utility.print_out(category, log_type, *args)


async def info(category, *args):
    await _log(category, 'INFO', *args)


async def error(category, *args):
    await _log(category, 'ERROR', *args)

