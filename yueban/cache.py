# -*- coding:utf-8 -*-

"""
Cache service: supply redis access
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


def get_connection_pool():
    return _redis_pool
