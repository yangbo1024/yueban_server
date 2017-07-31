# -*- coding:utf-8 -*-
"""
服务-工作
"""

import asyncio
from . import cache
from . import storage
from aiohttp import web
from . import utility
from . import communicate
from abc import ABCMeta
from abc import abstractmethod


_worker_app = None
_web_app = None


class Worker(object, metaclass=ABCMeta):
    def __init__(self):
        pass

    @abstractmethod
    async def on_proto(self, client_id, proto_id, proto_body):
        """
        客户端协议响应
        :param client_id:
        :param proto_id:
        :param proto_body:
        :return:
        """
        pass

    @abstractmethod
    async def on_client_closed(self, client_id):
        """
        某个客户端主动断开连接
        :param client_id:
        :return:
        """
        pass

    @abstractmethod
    async def on_call(self, method, args):
        """
        http调用响应
        :param method:
        :param args:
        :return:
        """
        pass


async def _yueban_handler(request):
    path = request.match_info['path']
    bs = await request.read()
    data = utility.loads(bs)
    if path == 'proto':
        # 来自客户端的协议
        client_id, proto_id, proto_body = data
        await _worker_app.on_proto(client_id, proto_id, proto_body)
        return web.Response(body=b'')
    elif path == 'client_closed':
        # 某个客户单断开连接
        client_id = data
        await _worker_app.on_client_closed(client_id)
        return web.Response(body=b'')
    else:
        return web.Response(body=b'')


async def _call_handler(request):
    path = request.match_info['path']
    bs = await request.read()
    data = utility.loads(bs)
    ret = await _worker_app.on_call(path, data)
    bs = utility.dumps(ret)
    return web.Response(body=bs)


async def call_later(seconds, method, args):
    """
    延时调用，定时器
    :param seconds: 多久之后调用，支持小数
    :param method:
    :param args:
    :return:
    """
    await communicate.post_scheduler('/yueban/schedule', [seconds, method, args])


async def _send_to_gate(gate_id, client_ids, proto_id, proto_body):
    await communicate.post_gate(gate_id, '/yueban/proto', [client_ids, proto_id, proto_body])


async def unicast(gate_id, client_id, proto_id, proto_body):
    """
    单播到某个网关
    :param gate_id:
    :param client_id:
    :param proto_id:
    :param proto_body:
    :return:
    """
    await _send_to_gate(gate_id, [client_id], proto_id, proto_body)


async def multicast(gate_id, client_ids, proto_id, proto_body):
    """
    多播到某个网关
    :param gate_id:
    :param client_ids:
    :param proto_id:
    :param proto_body:
    :return:
    """
    await _send_to_gate(gate_id, client_ids, proto_id, proto_body)


async def broadcast(proto_id, proto_body):
    """
    广播到所有网关
    :param proto_id:
    :param proto_body:
    :return:
    """
    await communicate.post_all_gates('/yueban/proto', [[], proto_id, proto_body])


async def close_clients(client_ids):
    """
    踢掉某些客户端
    :param client_ids:
    :return:
    """
    return await communicate.post_all_gates('/yueban/close_client', client_ids)


async def close_client(client_id):
    """
    踢掉某个客户端
    :param client_id:
    :return:
    """
    return await close_clients([client_id])


def get_web_app():
    return _web_app


def start(app):
    global _worker_app
    global _web_app
    if not isinstance(app, Worker):
        raise TypeError("bad worker app")
    _worker_app = app
    loop = asyncio.get_event_loop()
    loop.run_until_complete(cache.initialize())
    loop.run_until_complete(storage.initialize())
    _web_app = web.Application()
    _web_app.router.add_post('/yueban/{path}', _yueban_handler)
    _web_app.router.add_post('/call/{path}', _call_handler)
