# -*- coding:utf-8 -*-

"""
Time based call-later scheduler
"""

import asyncio
from aiohttp import web
from . import utility
from . import communicate
import filelock
import os.path
import time
from . import config


_web_app = None
_output_schedule = True
_locker = filelock.FileLock('yueban_lock')


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
    bs = await request.read()
    msg = utility.loads(bs)
    lock_name, timeout, interval = msg
    interval = max(interval, 0.0001)
    begin = time.time()
    while 1:
        if time.time() - begin >= timeout:
            return utility.pack_pickle_response(1)
        ok = False
        with _locker.acquire(timeout=timeout):
            if not os.path.exists(lock_name):
                ok = True
                with open(lock_name, 'w'):
                    pass
        if not ok:
            await asyncio.sleep(interval)
        else:
            return utility.pack_pickle_response(0)


async def _unlock_handler(request):
    bs = await request.read()
    msg = utility.loads(bs)
    lock_name = msg[0]
    with _locker.acquire():
        try:
            os.remove(lock_name)
            ok = True
        except Exception as e:
            utility.print_out(e)
            ok = False
    return utility.pack_pickle_response(ok)


async def _hotfix_handler(request):
    bs = await request.read()
    msg = utility.loads(bs)
    if msg != config.get_hotfix_password():
        return utility.pack_pickle_response('bad password')
    import importlib
    try:
        importlib.invalidate_caches()
        m = importlib.load_module('hotfix')
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


def start(output=True):
    global _web_app
    global _output_schedule
    _output_schedule = output
    _web_app = web.Application()
    _web_app.router.add_post('/yueban/schedule', _schedule_handler)
    _web_app.router.add_post('/yueban/lock', _lock_handler)
    _web_app.router.add_post('/yueban/unkock', _unlock_handler)
    _web_app.router.add_post('/yueban/hotfix', _hotfix_handler)
