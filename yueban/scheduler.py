# -*- coding:utf-8 -*-

"""
Time based call-later scheduler
"""

import asyncio
from aiohttp import web
from . import utility
from . import communicate
from . import config
from . import cache
from asyncio.queues import Queue
import yueban


LOCK_SCRIPT = """
redis.call("lpush", KEYS[1], KEYS[2])
if redis.call("llen", KEYS[1]) <= 1 then
    redis.call("lpush", KEYS[2], KEYS[1])
end
"""
UNLOCK_SCRIPT = """
redis.call("rpop", KEYS[1])
if redis.call("llen", KEYS[1]) > 0 then
    local k = redis.call("lindex", KEYS[1], -1)
    redis.call("lpush", k, KEYS[1])
end
"""


class LockInfo(object):
    def __init__(self):
        self.queue = Queue()
        self.ref = 0


_web_app = None
_output_schedule = True
_channel_id = ''
_locks = {}


async def _future(seconds, url, args):
    await asyncio.sleep(seconds)
    await communicate.post(url, args)


async def _schedule_handler(request):
    bs = await request.read()
    msg = utility.loads(bs)
    seconds, url, args = msg
    if _output_schedule:
        utility.print_out('schedule', seconds, url, args)
    asyncio.ensure_future(_future(seconds, url, args))
    return utility.pack_pickle_response('')


async def _lock_handler(request):
    redis = cache.get_connection_pool()
    bs = await request.read()
    msg = utility.loads(bs)
    lock_name = msg[0]
    if lock_name not in _locks:
        _locks[lock_name] = LockInfo()
    lock_info = _locks[lock_name]
    lock_info.ref += 1
    utility.print_out('lock_handler', lock_name)
    await redis.eval(LOCK_SCRIPT, keys=[lock_name, _channel_id])
    size = await redis.llen(lock_name)
    utility.print_out('lock_size', lock_name, size)
    await lock_info.queue.get()
    utility.print_out('got lock', lock_name)
    if lock_info.ref <= 0:
        _locks.pop(lock_name)
    return utility.pack_pickle_response(0)


async def _unlock_handler(request):
    bs = await request.read()
    msg = utility.loads(bs)
    lock_name = msg[0]
    redis = cache.get_connection_pool()
    utility.print_out('unlock_handler', lock_name)
    await redis.eval(UNLOCK_SCRIPT, keys=[lock_name])
    return utility.pack_pickle_response(0)


async def _hotfix_handler(request):
    bs = await request.read()
    msg = utility.loads(bs)
    if msg != config.get_hotfix_password():
        return utility.pack_pickle_response('bad password')
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
    utility.print_out('hotfix', result)
    return utility.pack_pickle_response(result)


def get_web_app():
    return _web_app


async def _yueban_handler(request):
    path = request.path
    if path == '/yueban/schedule':
        return await _schedule_handler(request)
    elif path == '/yueban/lock':
        return await _lock_handler(request)
    elif path == '/yueban/unlock':
        return await _unlock_handler(request)
    elif path == '/yueban/hotfix':
        return await _hotfix_handler(request)


async def _loop_rpop():
    global _channel_id
    redis = cache.get_connection_pool()
    inc_id = redis.incr(cache.INC_KEY)
    inc_str_id = '{0}'.format(inc_id)
    _channel_id = cache.make_key(cache.SYS_KEY_PREFIX, 'sc', inc_str_id)
    utility.print_out('loop_rpop_channel', _channel_id)
    while 1:
        msg = await redis.brpop(_channel_id)
        if not msg:
            utility.print_out('receive empty msg', _channel_id)
            continue
        lock_name = msg[1]
        lock_name = str(lock_name, 'utf8')
        lock_info = _locks.get(lock_name)
        utility.print_out('brpop lock', lock_name, lock_info, lock_info==None)
        if not lock_info:
            continue
        lock_info.ref -= 1
        lock_info.queue.put_nowait(1)


def start(output=True):
    global _web_app
    global _output_schedule
    _output_schedule = output
    yueban.initialize_with_file()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(cache.initialize())
    asyncio.ensure_future(_loop_rpop())
    _web_app = web.Application()
    _web_app.router.add_post('/yueban/{path}', _yueban_handler)
