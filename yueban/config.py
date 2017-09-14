# -*- coding:utf-8 -*-

"""
template:

{
    "redis": {
        "host": "10.0.30.26",
        "port": 20100,
        "password": "yj123456789.",
        "db": 0,
        "minsize": 1,
        "maxsize": 1
    },
    "mongodb": {
        "host": "10.0.30.26",
        "port": 20031,
        "password": "yj123456789.",
        "user": "game_yydz_mongodb",
        "db": "game_yydz",
        "replicaset": "",
        "min_pool_size": 2,
        "max_pool_size": 5
    },
    "gaters": {
        "huanan_1": {
            "id": "huanan_1",
            "host": "10.0.30.26",
            "port": 13100,
            "url": "http://10.0.30.26:13100",
            "ws_url": "ws://10.0.30.26:13100/"
        }
    },
    "scheduler_url": "http://10.0.30.26:13010",
    "worker_url": "http://10.0.30.26:13020",
    "csv_dir": "csv_table",
    "log_dir": "logs",
    "password": "Yueban1234"
}
"""

_config = {}


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


def get_all_gater_ids():
    cfg = _config['gaters']
    return list(cfg.keys())


def get_gate_config(gate_id):
    cfg = _config['gaters']
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

