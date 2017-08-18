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
from . import utility
from . import communicate
from . import config
import traceback
import time
import signal


_web_app = globals().setdefault('_web_app')
_gate_id = globals().setdefault('_gate_id', '')
_clients = globals().setdefault('_clients', {})


class Client(object):
    """
    A client object
    """
    def __init__(self, client_id, host, port):
        self.client_id = client_id
        self.host = host
        self.port = port
        self.send_task = None
        self.recv_task = None
        self.send_queue = None
        self.create_time = int(time.time())


def _add_client(client_id, host, port):
    client_obj = Client(client_id, host, port)
    _clients[client_id] = client_obj
    return client_obj


def remove_client(client_id):
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
    size = len(bs)
    if size < 4:
        utility.print_out('bad_proto_body', proto_body, bs)
        return None
    id_bs = bs[:4]
    proto_id = struct.unpack('>i', id_bs)[0]
    if size == 4:
        return proto_id, None
    body_bs = bs[4:]
    js = body_bs.decode('utf8')
    proto_object = json.loads(js)
    return proto_id, proto_object


async def _send_routine(client_obj, ws):
    client_id = client_obj.client_id
    queue = client_obj.send_queue
    while 1:
        try:
            msg = await queue.get()
            if msg is None:
                # only in _remove_client can be None
                utility.print_out('send_queue_none', client_id)
                break
            ws.send_bytes(msg)
        except Exception as e:
            utility.print_out('send_routine_error', client_id, e, traceback.format_exc())


async def _recv_routine(client_obj, ws):
    client_id = client_obj.client_id
    while 1:
        try:
            msg = await ws.receive()
            if msg.type == web.WSMsgType.BINARY:
                proto_id, proto_object = _unpack(msg.data)
                await communicate.post_game('/yueban/proto', [_gate_id, client_id, proto_id, proto_object])
            elif msg.type in (web.WSMsgType.CLOSE, web.WSMsgType.CLOSING, web.WSMsgType.CLOSED):
                remove_client(client_id)
                await communicate.post_game('/yueban/client_closed', [_gate_id, client_id])
                break
            elif msg.type == web.WSMsgType.ERROR:
                remove_client(client_id)
                await communicate.post_game('/yueban/client_closed', [_gate_id, client_id])
                utility.print_out('msg error', client_id)
                break
            else:
                utility.print_out("bad msg:", msg, msg.type)
        except Exception as e:
            utility.print_out('recv_routine_error', client_id, e, traceback.format_exc())


async def _websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    client_id = utility.gen_uniq_id()
    peer_name = request.transport.get_extra_info('peername')
    if peer_name is not None:
        client_host, client_port = peer_name
    else:
        client_host, client_port = '', 0
    client_obj = _add_client(client_id, client_host, client_port)
    client_obj.send_queue = asyncio.Queue()
    send_task = asyncio.ensure_future(_send_routine(client_obj, ws))
    recv_task = asyncio.ensure_future(_recv_routine(client_obj, ws))
    client_obj.send_task = send_task
    client_obj.recv_task = recv_task
    utility.print_out('serve_client', client_id, client_host, client_port)
    await asyncio.wait([send_task, recv_task], return_when=asyncio.FIRST_COMPLETED)
    return ws


async def _proto_handler(request):
    bs = await request.read()
    data = utility.loads(bs)
    client_ids, proto_id, proto_body = data
    if not client_ids:
        # broadcast
        client_ids = _clients.keys()
    for client_id in client_ids:
        client_obj = _clients.get(client_id)
        if not client_obj:
            continue
        q = client_obj.send_queue
        q.put_nowait(_pack(proto_id, proto_body))
    return utility.pack_pickle_response('')


async def _close_client_handler(request):
    bs = await request.read()
    data = utility.loads(bs)
    client_ids = data
    for client_id in client_ids:
        remove_client(client_id)
    return utility.pack_pickle_response('')


async def _get_online_cnt_handler(request):
    cnt = len(_clients)
    info = {
        'gate_id': _gate_id,
        'online': cnt,
        'config': config.get_gate_config(_gate_id),
    }
    bs = utility.dumps(info)
    return web.Response(body=bs)


async def _get_client_info_handler(request):
    bs = await request.read()
    data = utility.loads(bs)
    client_ids = data
    infos = {}
    for client_id in client_ids:
        client_obj = _clients.get(client_id)
        if not client_obj:
            continue
        infos[client_id] = {
            'host': client_obj.host,
        }
    bs = utility.dumps(infos)
    return web.Response(body=bs)


async def _get_all_clients_handler(request):
    bs = await request.read()
    data = utility.loads(bs)
    client_ids = _clients.keys()
    infos = {}
    for client_id in client_ids:
        client_obj = _clients.get(client_id)
        infos[client_id] = {
            'host': client_obj.host,
            'ctime': client_obj.create_time,
        }
    bs = utility.dumps(infos)
    return web.Response(body=bs)


async def _hotfix_handler(request):
    import importlib
    try:
        importlib.invalidate_caches()
        m = importlib.import_module('hotfix')
        importlib.reload(m)
        result = m.run()
    except Exception as e:
        import traceback
        result = [e, traceback.format_exc()]
    result = str(result)
    utility.print_out('hotfix', result)
    return utility.pack_pickle_response(result)


def get_gate_id():
    return _gate_id


def set_gate_id(gate_id):
    global _gate_id
    _gate_id = gate_id


def run(gate_id):
    global _web_app
    global _gate_id
    _gate_id = gate_id
    # web
    cfg = config.get_gate_config(gate_id)
    host = cfg['host']
    port = cfg['port']
    _web_app = web.Application()
    _web_app.router.add_get('/', _websocket_handler)
    _web_app.router.add_post('/yueban/proto', _proto_handler)
    _web_app.router.add_post('/yueban/close_client', _close_client_handler)
    _web_app.router.add_post('/yueban/get_online_cnt', _get_online_cnt_handler)
    _web_app.router.add_post('/yueban/get_client_info', _get_client_info_handler)
    _web_app.router.add_post('/yueban/get_all_clients', _get_all_clients_handler)
    _web_app.router.add_post('/yueban/hotfix', _hotfix_handler)
    web.run_app(_web_app, host=host, port=port)
