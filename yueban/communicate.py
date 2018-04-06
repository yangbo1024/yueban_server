# -*- coding:utf-8 -*-

"""
内部个服务之间交互
"""

import aiohttp
import asyncio
from . import config
from . import utility
import traceback


class GatePath(object):
    Proto = "/__proto"
    CloseClient = "/__close_client"
    GetOnlineCnt = "/__get_online_cnt"
    GetClientInfo = "/__get_client_info"
    Hotfix = "/__hotfix"
    
    
class WorkerPath(object):
    Proto = "/__proto"
    ClientClosed = "/__client_closed"
    OnSchedule = "/__on_schedule"


class SchedulePath(object):
    Schedule = "/__schedule"
    Hotfix = "/__hotfix"


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


async def post_gate(gate_id, path, args):
    base_url = config.get_gate_url(gate_id)
    url = '{0}{1}'.format(base_url, path)
    return await post(url, args)


async def post_all_gates(path, args):
    gate_ids = config.get_all_gate_ids()
    tasks = [post_gate(gate_id, path, args) for gate_id in gate_ids]
    results = await asyncio.gather(*tasks)
    return dict(zip(gate_ids, results))


async def post_scheduler(path, args):
    base_url = config.get_scheduler_url()
    url = '{0}{1}'.format(base_url, path)
    return await post(url, args)


async def post_worker(path, args):
    base_url = config.get_worker_url()
    url = '{0}{1}'.format(base_url, path)
    return await post(url, args)
