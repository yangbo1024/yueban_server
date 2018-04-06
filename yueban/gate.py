# -*- coding:utf-8 -*-

"""
网关
"""

from aiohttp import web
import json
import asyncio
from . import utility
from . import communicate
from . import config
import traceback
import time
from . import log


C2S_HEARTBEAT_PATH = "_hb"
S2C_HEARTBEAT_PATH = "_hb"
MAX_IDLE_TIME = 60


_web_app = globals().setdefault('_web_app')
_gate_id = globals().setdefault('_gate_id', '')
_clients = globals().setdefault('_clients', {})


class Client(object):
    """
    客户端对象，与客户端1：1存在
    """
    def __init__(self, client_id, host, port):
        self.client_id = client_id
        self.host = host
        self.port = port
        self.send_task = None
        self.recv_task = None
        self.send_queue = None
        self.create_time = int(time.time())


def log_info(*args):
    global _gate_id
    log.info(_gate_id, *args)


def log_error(*args):
    global _gate_id
    log.error(_gate_id, *args)


def set_heartbeat_path(c2s_path, s2c_path):
    global C2S_HEARTBEAT_PATH
    global S2C_HEARTBEAT_PATH
    C2S_HEARTBEAT_PATH = c2s_path
    S2C_HEARTBEAT_PATH = s2c_path
    log_info("set_heartbeat_path", c2s_path, s2c_path)


def set_max_idle_time(sec):
    global MAX_IDLE_TIME
    MAX_IDLE_TIME = sec


def _add_client(client_id, host, port):
    client_obj = Client(client_id, host, port)
    _clients[client_id] = client_obj
    return client_obj


def remove_client(client_id):
    client_obj = _clients.get(client_id)
    if not client_obj:
        return False
    try:
        client_obj.send_queue.put_nowait(None)
    except Exception as e:
        s = traceback.format_exc()
        log_error("remove_client_error", e, s)
    _clients.pop(client_id)
    return True


async def _send_routine(client_obj, ws):
    client_id = client_obj.client_id
    queue = client_obj.send_queue
    while 1:
        try:
            msg = await queue.get()
            if msg is None:
                # only in _remove_client can be None
                log_info('send_queue_none', client_id)
                break
            await ws.send_str(msg)
        except Exception as e:
            remove_client(client_id)
            log_error('send_routine_error', client_id, e, traceback.format_exc())
            break


async def _recv_routine(client_obj, ws):
    """
    接收处理客户端协议
    """
    client_id = client_obj.client_id
    while 1:
        try:
            msg = await ws.receive(timeout=MAX_IDLE_TIME)
            if msg.type == web.WSMsgType.TEXT:
                msg_object = json.loads(msg.data)
                path = msg_object["path"]
                if path == C2S_HEARTBEAT_PATH:
                    # 心跳协议直接在网关处理
                    q = client_obj.send_queue
                    msg_reply = {
                        "path": S2C_HEARTBEAT_PATH,
                        "body": {},
                        "time": time.time(),
                    }
                    reply_text = json.dumps(msg_reply)
                    await q.put(reply_text)
                else:
                    body = msg_object["body"]
                    await communicate.post_worker(communicate.WorkerPath.Proto, [_gate_id, client_id, path, body])
            else:
                remove_client(client_id)
                await communicate.post_worker(communicate.WorkerPath.ClientClosed, [_gate_id, client_id])
                break
        except Exception as e:
            remove_client(client_id)
            log_error('recv_routine_error', client_id, e, traceback.format_exc())
            await communicate.post_worker(communicate.WorkerPath.ClientClosed, [_gate_id, client_id])
            break


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
    client_obj.send_queue = asyncio.Queue(1024)
    send_task = asyncio.ensure_future(_send_routine(client_obj, ws))
    recv_task = asyncio.ensure_future(_recv_routine(client_obj, ws))
    client_obj.send_task = send_task
    client_obj.recv_task = recv_task
    log_info('serve_client', client_id, client_host, client_port, len(_clients))
    await asyncio.wait([send_task, recv_task], return_when=asyncio.FIRST_COMPLETED)
    log_info("finish_serve", client_id, len(_clients))
    return ws


async def _proto_handler(request):
    bs = await request.read()
    data = utility.loads(bs)
    client_ids, path, body = data
    if not client_ids:
        # broadcast
        client_ids = _clients.keys()
    try:
        msg_object = {
            "path": path,
            "body": body,
            "time": time.time(),
        }
        msg = json.dumps(msg_object)
    except Exception as e:
        s = traceback.format_exc()
        log_error("proto_dump_error", client_ids, path, body, e, s)
        return
    for client_id in client_ids:
        client_obj = _clients.get(client_id)
        if not client_obj:
            continue
        try:
            q = client_obj.send_queue
            q.put_nowait(msg)            
        except Exception as e:
            s = traceback.format_exc()
            log_error("proto_handler_error", client_id, path, body, e, s)
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
    if not client_ids:
        client_ids = _clients.keys()
    for client_id in client_ids:
        client_obj = _clients.get(client_id)
        if not client_obj:
            continue
        infos[client_id] = {
            'host': client_obj.host,
            'ctime': client_obj.create_time,
        }
    bs = utility.dumps(infos)
    return web.Response(body=bs)


async def _hotfix_handler(request):
    peer_name = request.transport.get_extra_info('peername')
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
    log_info('hotfix', peer_name, result)
    return utility.pack_json_response(result)


def get_gate_id():
    return _gate_id


def set_gate_id(gate_id):
    global _gate_id
    _gate_id = gate_id


_handlers = {
    communicate.GatePath.Proto: _proto_handler,
    communicate.GatePath.CloseClient: _close_client_handler,
    communicate.GatePath.GetOnlineCnt: _get_online_cnt_handler,
    communicate.GatePath.GetClientInfo: _get_client_info_handler,
    communicate.GatePath.Hotfix: _hotfix_handler,
}


async def _yueban_handler(request):
    handler = _handlers.get(request.path)
    if not handler:
        log_error('bad handler', request.path)
        return utility.pack_json_response(None)
    try:
        ret = await handler(request)
        return ret
    except Exception as e:
        s = traceback.format_exc()
        log_error("error", e, s)


async def _initialize():
    log.initialize()


def run(gate_id):
    global _web_app
    global _gate_id
    _gate_id = gate_id
    loop = asyncio.get_event_loop()
    loop.run_until_complete(_initialize())
    # web
    cfg = config.get_gate_config(gate_id)
    host = cfg['host']
    port = cfg['port']
    _web_app = web.Application()
    _web_app.router.add_get('/', _websocket_handler)
    _web_app.router.add_post('/{path:.*}', _yueban_handler)
    web.run_app(_web_app, host=host, port=port, access_log=None)
