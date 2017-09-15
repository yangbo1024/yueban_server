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


LOG_CATEGORY = 'yueban_schdule'


_slow_log_time = 0.1


class Lock(object):
    def __init__(self):
        self.ref = 0
        self.recv_queue = asyncio.PriorityQueue()


_web_app = globals().setdefault('_web_app')
_channel_id = globals().setdefault('_channel_id', '')
_locks = globals().setdefault('_locks', {})
_send_redis = globals().setdefault('_send_redis')
_recv_redis = globals().setdefault('_recv_redis')


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


def _ensure_get_lock(lock_name):
    if lock_name not in _locks:
        _locks[lock_name] = Lock()
    return _locks[lock_name]


def _check_remove_queue(lock_name):
    lock = _locks.get(lock_name)
    if not lock:
        return
    if lock.ref <= 0:
        _locks.pop(lock_name)


async def _lock_handler(request):
    begin = time.time()
    bs = await request.read()
    msg = utility.loads(bs)
    lock_name = msg[0]
    lock_key = cache.make_key(cache.LOCK_PREFIX, lock_name)
    # 一定要在push之前生成
    lock_obj = _ensure_get_lock(lock_name)
    lock_obj.ref += 1
    cnt = await _send_redis.lpush(lock_key, _channel_id)
    if cnt <= 1:
        lock_obj.ref -= 1
        _check_remove_queue(lock_name)
        return utility.pack_pickle_response(0)
    await lock_obj.recv_queue.get()
    lock_obj.ref -= 1
    _check_remove_queue(lock_name)
    used_time = time.time() - begin
    if used_time >= _slow_log_time:
        await log_info('slow_lock', used_time, _channel_id, msg)
    return utility.pack_pickle_response(0)


async def _unlock_handler(request):
    begin = time.time()
    bs = await request.read()
    msg = utility.loads(bs)
    lock_name = msg[0]
    lock_key = cache.make_key(cache.LOCK_PREFIX, lock_name)
    notify_channel = await _send_redis.rpop(lock_key)
    await _send_redis.lpush(notify_channel, lock_name)
    used_time = time.time() - begin
    if used_time >= _slow_log_time:
        await log_info('slow_unlock', used_time, _channel_id, msg)
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


async def _loop_brpop():
    while 1:
        try:
            msg = await _recv_redis.brpop(_channel_id)
            if not msg:
                await log_error('receive empty msg', _channel_id)
                continue
            tr = _recv_redis.multi_exec()
            tr.lrange(_channel_id, 0, -1)
            tr.delete(_channel_id)
            ret = await tr.execute()
            unlock_list = ret[0] or []
            first_bs = msg[1]
            unlock_list.insert(0, first_bs)
            for lock_name_bs in unlock_list:
                lock_name = str(lock_name_bs, 'utf-8')
                lock_obj = _locks[lock_name]
                lock_obj.recv_queue.put_nowait(1)
        except Exception as e:
            import traceback
            await log_error('loop_brpop error', e, traceback.format_exc())


async def initialize():
    global _channel_id
    global _send_redis
    global _recv_redis
    uniq_id = utility.gen_uniq_id()
    _channel_id = cache.make_key(cache.SYS_KEY_PREFIX, uniq_id)
    await log_info('loop_rpop_channel', _channel_id)
    await cache.initialize()
    _send_redis = cache.get_connection_pool()
    _recv_redis = await cache.create_connection_of_config()
    asyncio.ensure_future(_loop_brpop())


async def start():
    global _web_app
    _web_app = web.Application()
    _web_app.router.add_post('/yueban/{path}', _yueban_handler)
