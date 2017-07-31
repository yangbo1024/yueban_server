# -*- coding:utf-8 -*-

"""
service-gate functions:
    1. keep connections with clients
    2. handle client protocols
    3. push to client
"""

from aiohttp import web
import lz4.block as lz4block
import json
import struct
import asyncio
from . import log
from . import utility
from . import communicate
from . import config
from abc import ABCMeta
from abc import abstractmethod


_web_app = None
_gate_app = None
_clients = {}


class Gate(object, metaclass=ABCMeta):
    """
    网关对象
    """
    def __init__(self, gate_id):
        self.gate_id = gate_id

    @abstractmethod
    async def on_call(self, method, args):
        """
        当收到其它地方的调用的时候
        路径为/call/method
        :param method:
        :param args:
        :return:
        """
        pass


class Client(object):
    """
    一个客户端的信息对象
    """
    def __init__(self, client_id, host, port, send_task, recv_task):
        self.client_id = client_id
        self.host = host
        self.port = port
        self.send_task = send_task
        self.recv_task = recv_task
        self.send_queue = asyncio.Queue()


def get_gate_app():
    return _gate_app


def _add_client(client_id, host, port, send_task, recv_task):
    client_obj = Client(client_id, host, port, send_task, recv_task)
    _clients[client_id] = client_obj


def remove_client(client_id):
    """
    移除某个客户端
    :param client_id:
    :return:
    """
    client_obj = _clients.get(client_id)
    if not client_obj:
        return False
    client_obj.send_queue.put_nowait(None)
    _clients.pop(client_id)
    return True


def _pack(proto_id, proto_object):
    id_bs = struct.pack('>i', proto_id)
    js = json.dumps(proto_object)
    body_bs = bytes(js, 'utf8')
    bs = id_bs + body_bs
    bs = lz4block.compress(bs)
    return bs


def _unpack(proto_body):
    bs = lz4block.decompress(proto_body)
    if len(bs) <= 4:
        return None
    id_bs = bs[:4]
    body_bs = bs[4:]
    proto_id = struct.unpack('>i', id_bs)
    js = body_bs.decode('utf8')
    proto_object = json.loads(js)
    return proto_id, proto_object


async def _send_routine(client_obj, ws):
    queue = client_obj.send_queue
    while 1:
        msg = await queue.get()
        if msg is None:
            # 只有被移除的客户端才会放入None在队列中
            break
        ws.send_bytes(msg)


async def _recv_routine(client_id, ws):
    while 1:
        msg = await ws.receive()
        if msg.type == web.WSMsgType.BINARY:
            proto_id, proto_object = _unpack(msg.data)
            await communicate.post_worker('/yueban/proto', [client_id, proto_id, proto_object])
        elif msg.type in (web.WSMsgType.CLOSE, web.WSMsgType.CLOSING, web.WSMsgType.CLOSED):
            remove_client(client_id)
            await communicate.post_worker('/yueban/client_closed', [client_id])
            break
        elif msg.type == web.WSMsgType.ERROR:
            remove_client(client_id)
            await communicate.post_worker('/yueban/client_closed', [client_id])
            log.debug('msg error', client_id)
            break
        else:
            log.debug("bad msg:", msg, msg.type)


async def _websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    client_id = utility.gen_uniq_id()
    peer_name = request.transport.get_extra_info('peername')
    if peer_name is not None:
        client_host, client_port = peer_name
    else:
        client_host, client_port = '', 0
    send_task = asyncio.ensure_future(_send_routine(client_id, ws))
    recv_task = asyncio.ensure_future(_recv_routine(client_id, ws))
    _add_client(client_id, client_host, client_port, send_task, recv_task)
    await asyncio.wait([send_task, recv_task], return_when=asyncio.FIRST_COMPLETED)
    return ws


async def _yueban_handler(request):
    path = request.match_info['path']
    bs = await request.read()
    data = utility.loads(bs)
    if path == 'proto':
        client_ids, proto_id, proto_body = data
        if not client_ids:
            # 广播
            client_ids = _clients.keys()
        for client_id in client_ids:
            client_obj = _clients.get(client_id)
            if not client_obj:
                continue
            q = client_obj.send_queue
            q.put_nowait(_pack(proto_id, proto_body))
    elif path == 'close_client':
        client_ids = data
        for client_id in client_ids:
            remove_client(client_id)
        return web.Response(body=b'')
    else:
        return web.Response(body=b'')


async def _call_handler(request):
    path = request.match_info['path']
    bs = await request.read()
    data = utility.loads(bs)
    ret = await _gate_app.on_call(path, data)
    bs = utility.dumps(ret)
    return web.Response(body=bs)


def run(app):
    if not isinstance(app, Gate):
        raise TypeError("bad gate app")
    global _web_app
    global _gate_app
    _gate_app = app
    cfg = config.get_gate_config(app.gate_id)
    host = cfg['host']
    port = cfg['port']
    _web_app = web.Application()
    _web_app.router.add_get('/', _websocket_handler)
    _web_app.router.add_post('/yueban/{path}', _yueban_handler)
    _web_app.router.add_post('/call/{path}', _call_handler)
    web.run_app(_web_app, host=host, port=port)
