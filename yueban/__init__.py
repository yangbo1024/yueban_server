# -*- coding:utf-8 -*-
"""
name: 月半

dig:
         [...client1,client2...]
                    |
                    |
                websocket
                    |
                    |
          [...gater1,gater2...]]
                    |
                    |
                   http
                    |
                    |
          [...worker1,worker2...]   <---->   outer_http_request
                /         \
               /          \
        [redis_cache]     [mongodb_storage]

"""

import json
from . import config


__version__ = '1.3.8'


async def initialize(cfg):
    config.set_config(cfg)


async def initialize_with_file(file_path='yueban.conf'):
    with open(file_path) as f:
        s = f.read()
        cfg = json.loads(s)
        await initialize(cfg)
