# -*- coding:utf-8 -*-

"""
template:

cfg = {
    'cache_redis': {
        'host': '10.0.30.26',
        'port': 20100,
        'password': 'yj123456789.',
        'db': 0,
    },
    'data_mongodb': {
        'host': '10.0.30.26',
        'port': 20031,
        'password': 'yj123456789.',
        'user': 'game_yydz_mongodb',
        'db': 'game_yydz',
        'replicaset': '',
    },
    'stat_mongodb': {
        'host': '127.0.0.1',
        'port': 6379,
        'user': 'abc',
        'password': 'abcdef',
        'db': 'data',
        'replicaset': '',
    },
    'gaters': {
        'huanan_1': {
            'host': '127.0.0.1',
            'port': 10000,
            'url': 'http://127.0.0.1:10000',
        },
    },
    'worker_url': 'http://127.0.0.1:12345',
    'logger_url': 'http://127.0.0.1:12346',
    'scheduler_url': 'http://127.0.0.1:12347',
    'ums_url': 'http://127.0.0.1:12348',
    'cms_url': 'http://127.0.0.1:12349',
}
"""

import random


_config = {}


def set_config(config):
    global _config
    _config = config


def get_config():
    return _config


def get_cache_redis_config():
    cfg = _config['cache_redis']
    return cfg


def get_data_mongo_config():
    cfg = _config['data_mongodb']
    return cfg


def get_stat_mongo_config():
    cfg = _config['stat_mongodb']
    return cfg


def get_all_gater_ids():
    cfg = _config['gaters']
    return cfg.keys()


def get_gate_config(gate_id):
    cfg = _config['gaters']
    return cfg[gate_id]


def get_gate_url(gate_id):
    gate_config = get_gate_config(gate_id)
    return gate_config['url']


def get_worker_url():
    return _config['worker_url']


def get_logger_url():
    return _config['logger_url']


def get_scheduler_url():
    return _config['scheduler_url']


def get_ums_url():
    return _config['ums_url']


def get_cms_url():
    return _config['cms_url']