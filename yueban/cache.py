# -*- coding:utf-8 -*-

"""
redis数据读写，用于保存逻辑状态等
"""

import aioredis
from . import config


_redis_pool = None


SYS_KEY_PREFIX = 'yueban'


def make_key(fields):
    return ':'.join(fields)


async def initialize():
    global _redis_pool
    cfg = config.get_cache_redis_config()
    host = cfg['host']
    port = cfg['port']
    password = cfg['password']
    db = cfg['db']
    _redis_pool = await aioredis.create_pool((host, port), db=db, password=password)


def get_redis_pool():
    return _redis_pool
