# -*- coding:utf-8 -*-

"""
Communications between services
should be used by yueban only
"""

import aiohttp
import asyncio
from . import config
from . import utility
import traceback


async def post(url, args):
    try:
        data = utility.dumps(args)
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=data) as resp:
                bs = await resp.read()
                if resp.status != 200:
                    raise RuntimeError('{0}'.format(resp.status))
                return utility.loads(bs)
    except Exception as e:
        utility.print_out('post_error', url, args, e, traceback.format_exc())
        return None


async def post_gater(gate_id, path, args):
    base_url = config.get_gate_url(gate_id)
    url = '{0}{1}'.format(base_url, path)
    data = utility.dumps(args)
    return await post(url, data)


async def post_all_gaters(path, args):
    gate_ids = config.get_all_gater_ids()
    tasks = [post_gater(gate_id, path, args) for gate_id in gate_ids]
    results = await asyncio.gather(*tasks)
    return dict(zip(gate_ids, results))


async def post_logger(path, args):
    base_url = config.get_logger_url()
    url = '{0}{1}'.format(base_url, path)
    return await post(url, args)


async def post_scheduler(path, args):
    base_url = config.get_scheduler_url()
    url = '{0}{1}'.format(base_url, path)
    return await post(url, args)


async def post_game(path, args):
    base_url = config.get_game_url()
    url = '{0}{1}'.format(base_url, path)
    return await post(url, args)


async def post_ums(path, args):
    base_url = config.get_ums_url()
    url = '{0}{1}'.format(base_url, path)
    return await post(url, args)


async def post_cms(path, args):
    base_url = config.get_cms_url()
    url = '{0}{1}'.format(base_url, path)
    return await post(url, args)


async def call_later(seconds, url, args):
    """
    Call a method after some seconds with args
    :param seconds: float or int
    :param url:
    :param args:
    :return:
    """
    await post_scheduler('/yueban/schedule', [seconds, url, args])


async def call_game_later(seconds, path, args):
    game_url = config.get_game_url()
    url = game_url + path
    await call_later(seconds, url, args)


async def call_ums_later(seconds, path, args):
    ums_url = config.get_ums_url()
    url = ums_url + path
    await call_later(seconds, url, args)


async def call_cms_later(seconds, path, args):
    cms_url = config.get_cms_url()
    url = cms_url + path
    await call_later(seconds, url, args)