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
          [...gate1,gate2...]]
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
    一个mongodb(副本集）做数据存储

服务一共分为以下几类：
    1. gate
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

from . import config


__version__ = '2.2.7'


async def initialize(cfg):
    config.set_config(cfg)


async def initialize_with_file(file_path='yueban.conf'):
    config.load_config(file_path)
