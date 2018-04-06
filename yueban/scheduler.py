# -*- coding:utf-8 -*-

"""
调度服务 call_later
本服务业务简单，不能重启
如果有非常特殊的需求需要热更，可以用在线hotfix的方式逐个更新worker
"""

import asyncio
from aiohttp import web
from . import utility
from . import communicate
import time
from . import log
from yueban import config


_log_category = 'yueban_schdule'
_slow_log_time = 0.1


_web_app = None


async def log_info(*args):
    global _log_category
    log.info(_log_category, *args)


async def log_error(*args):
    global _log_category
    log.error(_log_category, *args)


def set_log_category(category):
    global _log_category
    _log_category = category


def get_log_category():
    return _log_category


def set_slow_log_time(seconds):
    global _slow_log_time
    _slow_log_time = max(seconds, 0.001)


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
        await log_error('schedule_error', url, args, e, traceback.format_exc())


async def _schedule_handler(request):
    bs = await request.read()
    msg = utility.loads(bs)
    seconds, url, args = msg
    asyncio.ensure_future(_future(seconds, url, args))
    return utility.pack_pickle_response('')


async def _hotfix_handler(request):
    peer_name = request.transport.get_extra_info('peername')
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
    await log_info('hotfix', peer_name, result)
    return utility.pack_json_response(result)


def get_web_app():
    return _web_app


async def _yueban_handler(request):
    path = request.path
    if path == communicate.SchedulePath.Schedule:
        ret = await _schedule_handler(request)
    elif path == communicate.SchedulePath.Hotfix:
        ret = await _hotfix_handler(request)
    else:
        ret = {}
        await log_error('bad_request_path', path)
    return ret


async def initialize():
    global _web_app
    _web_app = web.Application()
    _web_app.router.add_post('/{path:.*}', _yueban_handler)


async def start():
    pass
