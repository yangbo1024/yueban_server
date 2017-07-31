# -*- coding:utf-8 -*-

"""
时间调度服务
"""

import asyncio
from aiohttp import web
from . import utility
from . import communicate


_web_app = None


async def _schedule_handler(request):
    bs = await request.read()
    msg = utility.loads(bs)
    seconds, method, args = msg
    await asyncio.sleep(seconds)
    path = '/call/{0}'.format(method)
    await communicate.post_worker(path, args)


def get_web_app():
    return _web_app


def start():
    global _web_app
    _web_app = web.Application()
    _web_app.router.add_post('/yueban/schedule', _schedule_handler)