# -*- coding:utf-8 -*-
"""
框架名：月半

结构:
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
          [...worker1,worker2...]      <----- outer_http_request
                /         \
               /          \
        [redis_cache]     [mongodb_storage]

"""

from . import config


async def initialize(cfg):
    config.set_config(cfg)