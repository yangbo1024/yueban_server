# -*- coding:utf-8 -*-

"""
mongodb访问
有两个mongodb的连接：
    1. 数据
    2. 统计
"""

from motor import motor_asyncio
from . import config


_data_db_conn = None
_stat_db_conn = None


async def create_connection(host, port, database, user, password, replicaset='', min_pool_size=1, max_pool_size=5):
    client = motor_asyncio.AsyncIOMotorClient(host, port, replicaset=replicaset, minPoolSize=min_pool_size, maxPoolSize=max_pool_size)
    db = client[database]
    await db.authenticate(user, password)
    return db


async def create_data_connection():
    cfg = config.get_data_mongo_config()
    host = cfg['host']
    port = cfg['port']
    password = cfg['password']
    user = cfg['user']
    db = cfg['db']
    replicaset = cfg['replicaset']
    min_pool_size = cfg['min_pool_size']
    max_pool_size = cfg['max_pool_size']
    return await create_connection(host, port, db, user, password, replicaset, min_pool_size, max_pool_size)


async def initialize_data():
    global _data_db_conn
    _data_db_conn = await create_data_connection()


async def create_stat_connection():
    cfg = config.get_stat_mongo_config()
    host = cfg['host']
    port = cfg['port']
    password = cfg['password']
    user = cfg['user']
    db = cfg['db']
    replicaset = cfg['replicaset']
    min_pool_size = cfg['min_pool_size']
    max_pool_size = cfg['max_pool_size']
    return await create_connection(host, port, db, user, password, replicaset, min_pool_size, max_pool_size)


async def initialize_stat():
    global _stat_db_conn
    _stat_db_conn = await create_stat_connection()


def get_data_conn():
    return _data_db_conn


def get_stat_conn():
    return _stat_db_conn

