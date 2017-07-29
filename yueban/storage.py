# -*- coding:utf-8 -*-

"""
持久化存储
使用mongodb
"""

from motor import motor_asyncio
from . import config


# mongodb连接对象
_mongo_conn = None


async def create_connection(host, port, database, user, password, replicaset=''):
    """
    创建到mongo某个数据库的连接
    :param host:
    :param port:
    :param database:
    :param user:
    :param password:
    :param replicaset:
    :return:
    """
    client = motor_asyncio.AsyncIOMotorClient(host, port, replicaset=replicaset)
    db = client[database]
    await db.authenticate(user, password)
    return db


async def initialize():
    """
    :return:
    """
    global _mongo_conn
    cfg = config.get_data_mongo_config()
    host = cfg['host']
    port = cfg['port']
    password = cfg['password']
    user = cfg['user']
    db = cfg['db']
    replicaset = cfg['replicaset']
    _mongo_conn = await create_connection(host, port, db, user, password, replicaset)


def get_mongo_conn():
    """
    获取mongodb的连接
    :return:
    """
    return _mongo_conn
