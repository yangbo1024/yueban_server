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
          [...worker1,worker2...]      <----- outer_http_request
                /         \
               /          \
        [redis_cache]     [mongodb_storage]

"""

from . import config


__version__ = '0.9.1'


async def initialize(cfg):
    config.set_config(cfg)