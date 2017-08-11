# -*- coding:utf-8 -*-

"""
Time based call-later scheduler
"""

import asyncio
from aiohttp import web
from . import utility
from . import communicate
import signal


_web_app = None
_output_schedule = True


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


async def _hotfix_handler():
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
    return utility.pack_json_response(result)


def get_web_app():
    return _web_app


def start(output=True):
    global _web_app
    global _output_schedule
    _output_schedule = output
    _web_app = web.Application()
    _web_app.router.add_post('/yueban/schedule', _schedule_handler)
    loop = asyncio.get_event_loop()
    loop.add_signal_handler(signal.SIGILL, _hotfix_handler)
