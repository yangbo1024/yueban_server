# -*- coding:utf-8 -*-
"""
Service-worker
"""

from aiohttp import web
from . import utility
from . import communicate
from abc import ABCMeta
from abc import abstractmethod
from . import config


_worker_app = None
_web_app = None


class ProtocolMessage(object):
    __slots__ = ['gate_id', 'client_id', 'proto_id', 'proto_body', '_client_info']

    def __init__(self, gate_id, client_id, proto_id, proto_body):
        self.gate_id = gate_id
        self.client_id = client_id
        self.proto_id = proto_id
        self.proto_body = proto_body
        self._client_info = None

    async def get_client_info(self):
        """
        返回一个字典，里面包含客户端响应的信息
        :return: {host: ip_or_host}
        """
        if self._client_info is not None:
            return self._client_info
        ret = await communicate.post_gate(self.gate_id, '/yueban/get_client_info', [self.client_id])
        self._client_info = ret.get(self.client_id, {})
        return self._client_info

    def __str__(self):
        return 'ProtocolMessage(gate_id={0},client_id={1},proto_id={2},proto_body={3}'.format(
            self.gate_id, self.client_id, self.proto_id, self.proto_body
        )


class Worker(object, metaclass=ABCMeta):
    @abstractmethod
    async def on_call(self, request):
        pass

    @abstractmethod
    async def on_schedule(self, args):
        pass

    @abstractmethod
    async def on_proto(self, message):
        pass

    @abstractmethod
    async def on_client_closed(self, gate_id, client_id):
        pass


async def _yueban_handler(request):
    path = request.path
    bs = await request.read()
    data = utility.loads(bs)
    if path == '/yueban/proto':
        gate_id, client_id, proto_id, proto_body = data
        msg_obj = ProtocolMessage(gate_id, client_id, proto_id, proto_body)
        await _worker_app.on_proto(msg_obj)
        return utility.pack_pickle_response('')
    elif path == '/yueban/client_closed':
        gate_id, client_id = data
        await _worker_app.on_client_closed(gate_id, client_id)
        return utility.pack_pickle_response('')
    elif path == '/yueban/on_schedule':
        args = data
        await _worker_app.on_schedule(args)
        return utility.pack_pickle_response('')
    else:
        return utility.pack_pickle_response('')


async def _call_handler(request):
    return await _worker_app.on_call(request)


async def _send_to_gate(gate_id, client_ids, proto_id, proto_body):
    await communicate.post_gate(gate_id, '/yueban/proto', [client_ids, proto_id, proto_body])


async def unicast(gate_id, client_id, proto_id, proto_body):
    await _send_to_gate(gate_id, [client_id], proto_id, proto_body)


async def multicast(gate_id, client_ids, proto_id, proto_body):
    if not client_ids:
        return
    client_ids = list(client_ids)
    await _send_to_gate(gate_id, client_ids, proto_id, proto_body)


async def multicast_ex(client_ids, proto_id, proto_body):
    if not client_ids:
        return
    client_ids = list(client_ids)
    await communicate.post_all_gates('/yueban/proto', [client_ids, proto_id, proto_body])


async def broadcast(proto_id, proto_body):
    await communicate.post_all_gates('/yueban/proto', [[], proto_id, proto_body])


async def close_clients(client_ids):
    if not client_ids:
        return
    return await communicate.post_all_gates('/yueban/close_client', client_ids)


async def close_client(client_id):
    return await close_clients([client_id])


async def get_gate_online_cnt(gate_id):
    return await communicate.post_gate(gate_id, '/yueban/get_online_cnt', '')


async def get_all_gate_online():
    return await communicate.post_all_gates('/yueban/get_online_cnt', '')


async def get_client_infos_of_gate(gate_id, client_ids):
    return await communicate.post_gate(gate_id, '/yueban/get_client_info', client_ids)


async def get_all_client_infos(client_ids):
    return await communicate.post_all_gates('/yueban/get_client_info', client_ids)


async def get_all_clients_of_gate(gate_id):
    return await communicate.post_gate(gate_id, '/yueban/get_all_clients', [])


async def get_clients_of_all_gates():
    return await communicate.post_all_gates('/yueban/get_all_clients', [])


async def call_later(seconds, args):
    base_url = config.get_worker_url()
    url = base_url + '/yueban/on_schedule'
    return await communicate.post_scheduler('/yueban/schedule', [seconds, url, args])


def get_web_app():
    return _web_app


def get_worker_app():
    return _worker_app


async def start(app):
    global _worker_app
    global _web_app
    if not isinstance(app, Worker):
        raise TypeError("bad worker instance type")
    _worker_app = app
    _web_app = web.Application()
    _web_app.router.add_post('/yueban/{path}', _yueban_handler)
    _web_app.router.add_post('/call/{path:.*}', _call_handler)
