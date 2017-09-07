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


框架:
    基于aiohttp，aioredis, motor
    与客户端通过websocket进行长连接，内服服务用http短连进行通信

配置：
    参见config.py配置模板

数据库设计上为:
    一个redis做cache
    一个mongodb做数据存储
    一个mongodb数据库用于统计（非必须，且可与数据mongodb同库）

服务一共分为以下几类：
    1. gater
        游戏网关，和客户端用websocket直连，和游戏逻辑用http通信，实现桥接客户端和游戏逻辑的通信功能
    2. worker
        逻辑功能
    3. scheduler
        调度功能，包含定时调度和全局分布式锁

内嵌功能：
    1. cache
        redis访问
    2. storage
        mongodb访问
    3. log
        文件日志，按日切割，每个category分别一个文件
"""

import json
from . import config


__version__ = '1.5.6'


async def initialize(cfg):
    config.set_config(cfg)


async def initialize_with_file(file_path='yueban.conf'):
    with open(file_path) as f:
        s = f.read()
        cfg = json.loads(s)
        await initialize(cfg)
