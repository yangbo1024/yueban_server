# -*- coding:utf-8 -*-
"""
worker-逻辑进程，可以热更新
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
    def __init__(self, gate_id, client_id, path, body):
        self.gate_id = gate_id
        self.client_id = client_id
        self.path = path
        self.body = body
        self._client_info = None

    async def get_client_info(self):
        """
        返回一个字典，里面包含客户端响应的信息
        :return: 
        {
            "host": ip
        }
        """
        if self._client_info is not None:
            return self._client_info
        ret = await communicate.post_gate(self.gate_id, '/yueban/get_client_info', [self.client_id])
        self._client_info = ret.get(self.client_id, {})
        return self._client_info

    def __str__(self):
        return 'ProtocolMessage(gate_id={0},client_id={1},path={2},body={3}'.format(
            self.gate_id, self.client_id, self.path, self.body
        )


class Worker(object, metaclass=ABCMeta):
    @abstractmethod
    async def on_request(self, request):
        pass

    @abstractmethod
    async def on_schedule(self, args):
        pass

    @abstractmethod
    async def on_proto(self, message):
        """
        message是ProtocolMessage对象
        """
        pass

    @abstractmethod
    async def on_client_closed(self, gate_id, client_id):
        pass


async def _yueban_handler(request):
    path = request.path
    bs = await request.read()
    data = utility.loads(bs)
    if path == '/yueban/proto':
        gate_id, client_id, path, body = data
        msg_obj = ProtocolMessage(gate_id, client_id, path, body)
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


async def _request_handler(request):
    return await _worker_app.on_request(request)


async def _send_to_gate(gate_id, client_ids, path, body):
    await communicate.post_gate(gate_id, '/yueban/proto', [client_ids, path, body])


async def unicast(gate_id, client_id, path, body):
    """
    发送消息给一个gate的一个客户端连接
    """
    await _send_to_gate(gate_id, [client_id], path, body)


async def multicast(gate_id, client_ids, path, body):
    """
    发送消息给一个gate的多个客户端连接
    """
    if not client_ids:
        return
    client_ids = list(client_ids)
    await _send_to_gate(gate_id, client_ids, path, body)


async def multicast_ex(client_ids, path, body):
    """
    发送消息给多个客户端，不管客户端再哪个gate
    """
    if not client_ids:
        return
    client_ids = list(client_ids)
    await communicate.post_all_gates('/yueban/proto', [client_ids, path, body])


async def broadcast(path, body):
    """
    广播消息
    """
    await communicate.post_all_gates('/yueban/proto', [[], path, body])


async def close_clients(client_ids):
    """
    主动断开某些客户端连接
    """
    if not client_ids:
        return
    return await communicate.post_all_gates('/yueban/close_client', client_ids)


async def close_client(client_id):
    """
    断开一个客户端
    """
    return await close_clients([client_id])


async def get_gate_online_cnt(gate_id):
    """
    获取一个gate的在线人数
    返回格式:
    {
        'gate_id': _gate_id,
        'online': cnt,
        'config': config.get_gate_config(_gate_id),
    }
    """
    return await communicate.post_gate(gate_id, '/yueban/get_online_cnt', '')


async def get_all_gates_online():
    """
    获取所有gate的在线人数
    {
        gate_id:
        {
            'gate_id': _gate_id,
            'online': cnt,
            'config': config.get_gate_config(_gate_id),
        }
    }
    """
    return await communicate.post_all_gates('/yueban/get_online_cnt', '')


async def get_client_infos_of_gate(gate_id, client_ids):
    """
    获取单个gate的所有客户端的信息
    返回格式:
    {
        client_id:
        {
            "host": ip,
            "ctime": create_time,
        }
    }
    """
    return await communicate.post_gate(gate_id, '/yueban/get_client_info', client_ids)


async def get_all_client_infos(client_ids):
    """
    获取所有客户端的信息
    返回格式:
    {
        gate_id:
        {
            client_id:
            {
                "host": ip,
                "ctime": create_time,
            }
        }
    }
    """
    return await communicate.post_all_gates('/yueban/get_client_info', client_ids)


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
    _web_app.router.add_get("/yueban/request", _request_handler)
    _web_app.router.add_post("/yueban/request", _request_handler)