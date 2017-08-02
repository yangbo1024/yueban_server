# -*- coding:utf-8 -*-

"""
Cache service: supply redis access
"""

import aioredis
from . import config
from . import utility


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
    minsize = cfg['minsize']
    maxsize = cfg['maxsize']
    _redis_pool = await aioredis.create_pool((host, port), db=db, password=password, minsize=minsize, maxsize=maxsize)


def get_connection_pool():
    return _redis_pool


async def get_connection():
    return await _redis_pool.get_connection()


class Lock(object):
    """
    !! Do not use as possible as you can

    usage:
        async with Lock(lock_resource_name, timeout_seconds) as lock:
            if not lock:
                error_handle
            else:
                do_some_thing()
                print(lock.lock_id)
    """
    LOCK_SCRIPT = """
    redis.call('lpush', KEYS[1], KEYS[2])
    local l = redis.call('llen', KEYS[1])
    if (l <= 1)
    then
        return ''
    else
        return redis.call('lindex', KEYS[1], 1)
    end
    """
    UNLOCK_SCRIPT = """
    local k = redis.call('rpop', KEYS[1])
    local l = redis.call('llen', KEYS[1])
    if (l <= 0)
    then
        return k
    else
        redis.call('lpush', k, '')
        return k
    end
    """

    def __init__(self, lock_name, timeout=5):
        self.lock_key = make_key(SYS_KEY_PREFIX, lock_name)
        self.lock_id = utility.gen_uniq_id()
        self.timeout = int(timeout)

    async def __aenter__(self):
        waiting_key = await _redis_pool.execute('eval', self.LOCK_SCRIPT, 2, self.lock_key, self.lock_id)
        if not waiting_key:
            return self
        wait_ret = await _redis_pool.execute('brpop', waiting_key, self.timeout)
        if not wait_ret:
            return None
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await _redis_pool.execute('eval', self.UNLOCK_SCRIPT, 1, self.lock_key)
