# -*- coding:utf-8 -*-

"""
redis访问
"""

import aioredis
from . import config
import time


_redis_pool = None


# 以SYS_KEY_PREFIX开头的key，是系统保留key
SYS_KEY_PREFIX = '_y'
LOCK_PREFIX = '{0}:lock'.format(SYS_KEY_PREFIX)


def make_key(*fields):
    return ':'.join(fields)


async def create_pool(host, port, password, db, minsize, maxsize):
    return await aioredis.create_redis_pool((host, port), db=db, password=password, minsize=minsize, maxsize=maxsize)


async def create_pool_of_config():
    global _redis_pool
    cfg = config.get_redis_config()
    host = cfg['host']
    port = cfg['port']
    password = cfg['password']
    db = cfg['db']
    minsize = cfg['minsize']
    maxsize = cfg['maxsize']
    return await create_pool(host, port, password, db, minsize, maxsize)


async def create_pool_with_custom_size(minsize, maxsize):
    global _redis_pool
    cfg = config.get_redis_config()
    host = cfg['host']
    port = cfg['port']
    password = cfg['password']
    db = cfg['db']
    return await create_pool(host, port, password, db, minsize, maxsize)


async def initialize():
    global _redis_pool
    _redis_pool = await create_pool_of_config()


def get_connection_pool():
    return _redis_pool


class Lock(object):
    """
    效率低，少用
    usage:
        async with Lock(lock_resource_name, timeout_seconds) as lock:
            if not lock:
                error_handle
            else:
                do_some_thing()
                print(lock.lock_id)
    """
    UNLOCK_SCRIPT = """
    if redis.call("get", KEYS[1]) == ARGV[1] then
        return redis.call("del", KEYS[1])
    else
        return 0
    end
    """

    def __init__(self, lock_name, timeout=5.0, interval=0.01, lua_valid=True):
        # 很大一部分云服务提供商的redis不支持lua，所以默认不采用lua辅助实现
        from . import utility
        self.lock_key = make_key(SYS_KEY_PREFIX, lock_name)
        self.lock_id = utility.gen_uniq_id()
        self.timeout = max(0.02, timeout)
        self.interval = max(0.001, interval)
        self.lua_valid = lua_valid
        self.begin_time = time.time()

    async def __aenter__(self):
        import asyncio
        nx = _redis_pool.SET_IF_NOT_EXIST
        p_timeout = int(self.timeout * 1000)
        p_interval = int(self.interval * 1000)
        p_sum_time = 0
        while p_sum_time < p_timeout:
            ok = await _redis_pool.set(self.lock_key, self.lock_id, pexpire=p_timeout, exist=nx)
            if not ok:
                await asyncio.sleep(self.interval)
                p_sum_time += p_interval
                continue
            return self
        from . import utility
        utility.print_out("lock failed", self.lock_key, self.lock_id, self.timeout)
        return None

    async def __aexit__(self, exc_type, exc, tb):
        if exc_type:
            import traceback
            from . import utility
            el = traceback.format_exception(exc_type, exc, tb)
            es = "".join(el)
            utility.print_out('lock_exc_error:\n', es)
        if self.lua_valid:
            await _redis_pool.eval(self.UNLOCK_SCRIPT, keys=[self.lock_key], args=[self.lock_id])
        else:
            locked_id = await _redis_pool.get(self.lock_key)
            if locked_id == self.lock_id:
                await _redis_pool.delete(self.lock_key)
        used_time = time.time() - self.begin_time
        if used_time >= 1.0:
            from . import utility
            utility.print_out("slow_lock", self.lock_key, used_time)
