# -*- coding:utf-8 -*-

"""
template:

{
    "cache_redis": {
        "host": "10.0.30.26",
        "port": 20100,
        "password": "yj123456789.",
        "db": 0,
        "minsize": 1,
        "maxsize": 2
    },
    "data_mongodb": {
        "host": "10.0.30.26",
        "port": 20031,
        "password": "yj123456789.",
        "user": "game_yydz_mongodb",
        "db": "game_yydz",
        "replicaset": ""
    },
    "stat_mongodb": {
        "host": "10.0.30.26",
        "port": 20031,
        "password": "yj123456789.",
        "user": "game_yydz_mongodb",
        "db": "game_yydz",
        "replicaset": "",
        "log_collection": "yueban_log",
        "log_expire": 5184000
    },
    "gaters": {
        "huanan_1": {
            "host": "10.0.30.26",
            "port": 13100,
            "url": "http://10.0.30.26:13100",
            "ws_url": "ws://10.0.30.26:13100/"
        }
    },
    "logger_url": "http://10.0.30.26:13000",
    "scheduler_url": "http://10.0.30.26:13010",
    "game_url": "http://10.0.30.26:13020",
    "ums_url": "http://10.0.30.26:13030",
    "cms_url": "http://10.0.30.26:13040",
    "csv_dir": "csv_table"
}
"""

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


def get_logger_url():
    return _config['logger_url']


def get_scheduler_url():
    return _config['scheduler_url']


def get_game_url():
    return _config['game_url']


def get_ums_url():
    return _config['ums_url']


def get_cms_url():
    return _config['cms_url']


def get_csv_dir():
    return _config['csv_dir']


def get_log_collection():
    cfg = _config['stat_mongodb']
    return cfg['log_collection']


def get_log_expire_seconds():
    cfg = _config['stat_mongodb']
    return cfg['log_expire']
