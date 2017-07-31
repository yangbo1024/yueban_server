# -*- coding:utf-8 -*-

"""
Log functions
"""

from . import communicate


def debug(*args):
    """
    Only print to std(err)
    :param args:
    :return:
    """
    s = " ".join([str(arg) for arg in args])
    print(s)


async def log(*args):
    """
    Log to a single file use logging
    :param args:
    :return:
    """
    if not args:
        return
    s = " ".join([str(arg) for arg in args])
    await communicate.post_logger('log', s)


async def stat(collection_name, documents):
    """
    Stats to MongoDB
    :param collection_name:
    :param documents:
    :return:
    """
    await communicate.post_logger('stat', [collection_name, documents])
