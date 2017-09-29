# -*- coding:utf-8 -*-

"""
configuration
"""

_config = {
    "redis": {
        "host": "123.123.123.123",
        "port": 12345,
        "password": "password",
        "db": 0,
        "minsize": 1,
        "maxsize": 1
    },
    "mongodb": {
        "host": "123.123.123.123",
        "port": 12345,
        "password": "password",
        "user": "user",
        "db": "db",
        "replicaset": "",
        "min_pool_size": 2,
        "max_pool_size": 5
    },
    "gates": {
        "huanan_1": {
            "id": "huanan_1",
            "host": "123.123.123.123",
            "port": 12345,
            "url": "http://123.123.123.123:13100",
            "ws_url": "ws://123.123.123.123:13100/"
        }
    },
    "scheduler_url": "123.123.123.123:13010",
    "worker_url": "http://123.123.123.123:13020",
    "csv_dir": "csv_table",
    "log_dir": "logs",
    "password": "Yueban1234"
}


def load_config(file_path):
    import json
    global _config
    with open(file_path) as f:
        s = f.read()
        cfg = json.loads(s)
        _config = cfg


def set_config(config):
    global _config
    _config = config


def get_config():
    return _config


def get_redis_config():
    cfg = _config['redis']
    return cfg


def get_mongodb_config():
    cfg = _config['mongodb']
    return cfg


def get_all_gate_ids():
    cfg = _config['gates']
    return list(cfg.keys())


def get_gate_config(gate_id):
    cfg = _config['gates']
    return cfg[gate_id]


def get_gate_url(gate_id):
    gate_config = get_gate_config(gate_id)
    return gate_config['url']


def get_scheduler_url():
    return _config['scheduler_url']


def get_worker_url():
    return _config['worker_url']


def get_csv_dir():
    return _config['csv_dir']


def get_log_dir():
    return _config['log_dir']


def get_password():
    return _config['password']

