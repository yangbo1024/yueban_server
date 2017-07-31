# -*- coding:utf-8 -*-

"""
communications between services
"""

import aiohttp
import asyncio
from . import config
from . import utility


async def post(url, args):
    data = utility.dumps(args)
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=data) as resp:
            bs = await resp.read()
            return utility.loads(bs)


async def post_worker(path, args):
    base_url = config.get_worker_url()
    url = '{0}/{1}'.format(base_url, path)
    data = utility.dumps(args)
    return await post(url, data)


async def post_gate(gate_id, path, args):
    base_url = config.get_gate_url(gate_id)
    url = '{0}/{1}'.format(base_url, path)
    data = utility.dumps(args)
    return await post(url, data)


async def post_all_gates(path, args):
    gate_ids = config.get_all_gater_ids()
    tasks = [post_gate(gate_id, path, args) for gate_id in gate_ids]
    results = await asyncio.gather(*tasks)
    return dict(zip(gate_ids, results))


async def post_logger(path, args):
    base_url = config.get_logger_url()
    url = '{0}/{1}'.format(base_url, path)
    data = utility.dumps(args)
    return await post(url, data)


async def post_scheduler(path, args):
    base_url = config.get_scheduler_url()
    url = '{0}/{1}'.format(base_url, path)
    data = utility.dumps(args)
    return await post(url, data)