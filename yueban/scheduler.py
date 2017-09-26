# -*- coding:utf-8 -*-

"""
调度服务
    1. call_later
    2. 全局锁
本服务业务简单，不能重启
如果有非常特殊的需求需要热更，可以用在线hotfix的方式
"""

import asyncio
from aiohttp import web
from . import utility
from . import communicate
from . import cache
import time
from yueban import log as yueban_log


# KEYS = [lock_key]
UNLOCK_SCRIPT = """
redis.call("rpop", KEYS[1])
local k = redis.call("lindex", KEYS[1], -1)
if k then
    redis.call("publish", k, "")
end
"""


LOG_CATEGORY = 'yueban_schdule'

_slow_log_time = 0.1
_pid = None
_inc = 0
_web_app = None
_send_redis = None
_recv_redis = None


def gen_lock_id():
    global _pid
    global _inc
    _inc = (_inc + 1) % 65536
    t = time.time()
    return "{0}_{1:06f}_{2}".format(_pid, t, _inc)


async def log_info(*args):
    await yueban_log.info(LOG_CATEGORY, *args)


async def log_error(*args):
    await yueban_log.error(LOG_CATEGORY, *args)


def set_slow_log_time(seconds):
    global _slow_log_time
    _slow_log_time = max(seconds, 0)


def get_slow_log_time():
    return _slow_log_time


async def _future(seconds, url, args):
    await asyncio.sleep(seconds)
    try:
        begin = time.time()
        await communicate.post(url, args)
        used_time = time.time() - begin
        if used_time >= _slow_log_time:
            await log_info('slow_schedule_post', used_time, url, args)
    except Exception as e:
        import traceback
        await log_error('sche_error', url, args, e, traceback.format_exc())


async def _schedule_handler(request):
    bs = await request.read()
    msg = utility.loads(bs)
    seconds, url, args = msg
    asyncio.ensure_future(_future(seconds, url, args))
    return utility.pack_pickle_response('')


async def _lock_handler(request):
    begin = time.time()
    bs = await request.read()
    msg = utility.loads(bs)
    lock_name = msg[0]
    lock_id = gen_lock_id()
    lock_key = cache.make_key(cache.LOCK_PREFIX, lock_name)
    cnt = await _send_redis.lpush(lock_key, lock_id)
    if cnt <= 1:
        return utility.pack_pickle_response(0)
    redis = await _recv_redis.acquire()
    await redis.brpop(lock_id)
    used_time = time.time() - begin
    if used_time >= _slow_log_time:
        await log_info('slow_lock', used_time, _pid, msg)
    return utility.pack_pickle_response(0)


async def _unlock_handler(request):
    bs = await request.read()
    msg = utility.loads(bs)
    lock_name = msg[0]
    lock_key = cache.make_key(cache.LOCK_PREFIX, lock_name)
    await _send_redis.eval(UNLOCK_SCRIPT, keys=[lock_key])
    return utility.pack_pickle_response(0)


async def _hotfix_handler(request):
    peername = request.transport.get_extra_info('peername')
    import importlib
    try:
        importlib.invalidate_caches()
        m = importlib.import_module('hotfix')
        importlib.reload(m)
        result = m.run()
    except Exception as e:
        import traceback
        result = [e, traceback.format_exc()]
    result = str(result)
    await log_info('hotfix', peername, result)
    return utility.pack_json_response(result)


def get_web_app():
    return _web_app


async def _yueban_handler(request):
    path = request.path
    if path == '/yueban/schedule':
        ret = await _schedule_handler(request)
    elif path == '/yueban/lock':
        ret = await _lock_handler(request)
    elif path == '/yueban/unlock':
        ret = await _unlock_handler(request)
    elif path == '/yueban/hotfix':
        ret = await _hotfix_handler(request)
    else:
        ret = {}
        await log_error('bad_request_path', path)
    return ret


async def initialize(min_lock_pool_size=5, max_lock_pool_size=10):
    global _send_redis
    global _recv_redis
    global _pid
    import os
    _pid = os.getpid()
    await cache.initialize()
    _send_redis = cache.get_connection_pool()
    _recv_redis = await cache.create_pool_with_custom_size(min_lock_pool_size, max_lock_pool_size)


async def start():
    global _web_app
    _web_app = web.Application()
    _web_app.router.add_post('/yueban/{path}', _yueban_handler)
