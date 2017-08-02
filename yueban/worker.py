# -*- coding:utf-8 -*-
"""
Service-worker
"""

from aiohttp import web
from . import utility
from . import communicate
from abc import ABCMeta
from abc import abstractmethod
import json
from . import config


_worker_app = None
_web_app = None


class _BaseWorker(object, metaclass=ABCMeta):
    @abstractmethod
    async def on_call(self, request):
        pass


class UMSWorker(_BaseWorker):
    pass


class CMSWorker(_BaseWorker):
    pass


class GameWorker(_BaseWorker):
    @abstractmethod
    async def on_proto(self, client_id, proto_id, proto_body):
        """
        Called when received a proto of a client
        :param client_id:
        :param proto_id:
        :param proto_body:
        :return:
        """
        pass

    @abstractmethod
    async def on_client_closed(self, client_id):
        """
        Called when a client shut the connection
        :param client_id:
        :return:
        """
        pass


async def _yueban_handler(request):
    path = request.path
    bs = await request.read()
    data = utility.loads(bs)
    if path == '/yueban/proto':
        client_id, proto_id, proto_body = data
        await _worker_app.on_proto(client_id, proto_id, proto_body)
        return web.Response(body=b'')
    elif path == '/yueban/client_closed':
        client_id = data
        await _worker_app.on_client_closed(client_id)
        return web.Response(body=b'')
    else:
        return web.Response(body=b'')


async def _call_handler(request):
    return await _worker_app.on_call(request)


async def call_later(seconds, url, args):
    """
    Call a method after some seconds with args
    :param seconds: float or int
    :param url:
    :param args:
    :return:
    """
    await communicate.post_scheduler('/yueban/schedule', [seconds, url, args])


async def _send_to_gate(gate_id, client_ids, proto_id, proto_body):
    await communicate.post_gater(gate_id, '/yueban/proto', [client_ids, proto_id, proto_body])


async def unicast(gate_id, client_id, proto_id, proto_body):
    """
    Send to one client
    :param gate_id:
    :param client_id:
    :param proto_id:
    :param proto_body:
    :return:
    """
    await _send_to_gate(gate_id, [client_id], proto_id, proto_body)


async def multicast(gate_id, client_ids, proto_id, proto_body):
    """
    Send to multiple clients
    :param gate_id:
    :param client_ids:
    :param proto_id:
    :param proto_body:
    :return:
    """
    if not client_ids:
        return
    await _send_to_gate(gate_id, client_ids, proto_id, proto_body)


async def multicast_ex(client_ids, proto_id, proto_body):
    """
    Send to all gates of clients
    :param client_ids:
    :param proto_id:
    :param proto_body:
    :return:
    """
    if not client_ids:
        return
    await communicate.post_all_gaters('/yueban/proto', [client_ids, proto_id, proto_body])


async def broadcast(proto_id, proto_body):
    """
    Send to all clients
    :param proto_id:
    :param proto_body:
    :return:
    """
    await communicate.post_all_gaters('/yueban/proto', [[], proto_id, proto_body])


async def close_clients(client_ids):
    """
    Close some clients
    :param client_ids:
    :return:
    """
    if not client_ids:
        return
    return await communicate.post_all_gaters('/yueban/close_client', client_ids)


async def close_client(client_id):
    """
    Close only 1 client
    :param client_id:
    :return:
    """
    return await close_clients([client_id])


async def get_gater_online_cnt(gate_id):
    return await communicate.post_gater(gate_id, '/yueban/get_online_cnt', '')


async def get_all_gater_online():
    return await communicate.post_all_gaters('/yueban/get_online_cnt', '')


def get_web_app():
    return _web_app


def start(app):
    global _worker_app
    global _web_app
    if not isinstance(app, _BaseWorker):
        raise TypeError("bad worker instance type")
    _worker_app = app
    _web_app = web.Application()
    _web_app.router.add_post('/yueban/{path}', _yueban_handler)
    _web_app.router.add_post('/call/{path:.*}', _call_handler)
