# -*- coding:utf-8 -*-

"""
持久化存储
使用mongodb
"""

from motor import motor_asyncio
from . import config


# mongodb连接对象
_data_db_conn = None
_stat_db_conn = None


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


async def initialize_data():
    """
    :return:
    """
    global _data_db_conn
    cfg = config.get_data_mongo_config()
    host = cfg['host']
    port = cfg['port']
    password = cfg['password']
    user = cfg['user']
    db = cfg['db']
    replicaset = cfg['replicaset']
    _data_db_conn = await create_connection(host, port, db, user, password, replicaset)


async def initialize_stat():
    global _stat_db_conn
    cfg = config.get_stat_mongo_config()
    host = cfg['host']
    port = cfg['port']
    password = cfg['password']
    user = cfg['user']
    db = cfg['db']
    replicaset = cfg['replicaset']
    _stat_db_conn = await create_connection(host, port, db, user, password, replicaset)


def get_data_conn():
    """
    获取数据-mongodb的连接
    :return:
    """
    return _data_db_conn


def get_stat_conn():
    return _stat_db_conn

