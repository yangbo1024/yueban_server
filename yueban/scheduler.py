# -*- coding:utf-8 -*-

"""
Time based call-later scheduler
"""

import asyncio
from aiohttp import web
from . import utility
from . import communicate
from . import log


_web_app = None


async def _schedule_handler(request):
    bs = await request.read()
    msg = utility.loads(bs)
    seconds, path, args = msg
    log.debug()
    await asyncio.sleep(seconds)
    await communicate.post_worker(path, args)


def get_web_app():
    return _web_app


def start():
    global _web_app
    _web_app = web.Application()
    _web_app.router.add_post('/yueban/schedule', _schedule_handler)