# -*- coding:utf-8 -*-

"""
日志系统: 采用文本存储，适用于：不重要，无需统计，用于调试，或者短时间之内的需求不定需求的查询
"""

from . import communicate


def debug(*args):
    """
    应用逻辑调试日志，不存盘
    :param args: 每个参数须支持str转化
    :return:
    """
    s = " ".join([str(arg) for arg in args])
    print(s)


async def log(*args):
    """
    应用逻辑信息日志
    :param args: 每个参数须支持str转化
    :return:
    """
    if not args:
        return
    s = " ".join([str(arg) for arg in args])
    await communicate.post_logger('log', s)


async def stat(collection_name, documents):
    """
    统计信息，存盘进入mongodb
    :param collection_name:
    :param documents:
    :return:
    """
    await communicate.post_logger('stat', [collection_name, documents])
