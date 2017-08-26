# -*- coding:utf-8 -*-

"""
日志函数
需要用到日志的地方，需要先初始化cache
每个日志文件以category命名，按日切割
注意category要全局唯一，如果多个master进程部署，每个部署的服务不能共享同样的category
"""

from . import utility
from . import cache
from . import config
from datetime import datetime
import os
import shutil


_log_files = {}


async def _get_log_file(category):
    log_dir = config.get_log_dir()
    path = os.path.join(log_dir, category)
    path += '.log'
    if category not in _log_files:
        f = open(path, 'a', buffering=1)
        _log_files[category] = f
        return f
    try:
        stat_info = os.stat(path)
    except FileNotFoundError:
        f = open(path, 'a', buffering=1)
        _log_files[category] = f
        return
    mdt = datetime.fromtimestamp(stat_info.st_mtime)
    now = datetime.now()
    # 跨天
    if mdt.day != now.day:
        f = _log_files[category]
        f.close()
        src = path
        postfix = mdt.strftime('%Y%m%d')
        dst = '{0}.{1}'.format(path, postfix)
        log_key = cache.make_key(cache.LOG_PREFIX, category, postfix)
        redis = cache.get_connection_pool()
        expire = 2 * 86400 + 1
        ok = await redis.set(log_key, postfix, expire=expire, exist=redis.SET_IF_NOT_EXIST)
        if ok:
            shutil.move(src, dst)
        f = open(path, 'a', buffering=1)
        _log_files[category] = f
    return _log_files[category]


async def _log(category, log_type, *args):
    if not args:
        return
    f = await _get_log_file(category)
    now = datetime.now()
    time_str = now.strftime('%Y-%m-%d %H:%M:%S,%f')[:23]
    sl = [time_str, log_type]
    sl.extend([str(arg) for arg in args])
    sl.append(os.linesep)
    s = ' '.join(sl)
    f.write(s)


async def info(category, *args):
    await _log(category, 'INFO', *args)


async def error(category, *args):
    await _log(category, 'ERROR', *args)


async def initialize():
    log_dir = config.get_log_dir()
    utility.ensure_directory(log_dir)


async def clear():
    for _, log_file in _log_files.items():
        try:
            log_file.close()
        except:
            pass
    _log_files.clear()

