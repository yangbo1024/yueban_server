# -*- coding:utf-8 -*-

"""
日志函数
需要用到日志的地方，需要先初始化cache
每个日志文件以category命名，按日切割
注意category要全局唯一，如果多个master进程部署，每个部署的服务不能共享同样的category
"""

from . import utility
from . import config
from datetime import datetime
import os


class LogFile(object):
    def __init__(self, mdt, f):
        self.mdt = mdt
        self.f = f


_log_files = {}


def _create_file_obj(path, mdt):
    f = open(path, 'a', buffering=1)
    file_obj = LogFile(mdt, f)
    return file_obj


async def _get_log_file(category):
    log_dir = config.get_log_dir()
    path = os.path.join(log_dir, category)
    path += '.log'
    now = datetime.now()
    if category not in _log_files:
        try:
            stat_info = os.stat(path)
            mdt = datetime.fromtimestamp(stat_info.st_mtime)
        except FileNotFoundError:
            mdt = now
        _log_files[category] = _create_file_obj(path, mdt)
    file_obj = _log_files[category]
    mdt = file_obj.mdt
    # 跨天
    if mdt.day != now.day:
        src = path
        postfix = mdt.strftime('%Y%m%d')
        dst = '{0}.{1}'.format(path, postfix)
        if not os.path.exists(dst):
            try:
                os.rename(src, dst)
            except Exception as e:
                utility.print_out('rename error', src, dst, e, category)
        file_obj.f.close()
        file_obj = _create_file_obj(src, now)
        _log_files[category] = file_obj
    return file_obj.f


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

