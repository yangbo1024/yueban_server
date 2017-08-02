"""
Service-collect log or stats:
"""

import asyncio
import logging
import logging.handlers
import os
import os.path
import filelock
import time
from logging.handlers import TimedRotatingFileHandler
from aiohttp import web
from . import utility
from . import storage


_web_app = None
_loggers = {}


def ensure_logger(category, log_name='yueban.log'):
    global _loggers
    _logger = logging.getLogger('')
    _logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s %(message)s")
    if not os.path.exists(category):
        os.makedirs(category)
    handler = MultiProcessTimedRotatingFileHandler(log_name, when="midnight")
    handler.suffix = "%Y%m%d"
    handler.setFormatter(formatter)
    _logger.addHandler(handler)
    _loggers[category] = log_name


def get_logger(category):
    ensure_logger(category)
    return _loggers[category]


async def initialize():
    await storage.initialize_stat()


class Logger(object):
    def __init__(self, log_name):
        self.log_name = log_name

    def on_message(self, msg_type, args):
        pass


class MultiProcessTimedRotatingFileHandler(TimedRotatingFileHandler):
    """
    MultiProcess with a same log-file
    """
    def doRollover(self):
        """
        do a rollover; in this case, a date/time stamp is appended to the filename
        when the rollover happens.  However, you want the file to be named for the
        start of the interval, not the current time.  If there is a backup count,
        then we have to get a list of matching filenames, sort them and remove
        the one with the oldest suffix.
        """
        #if self.stream:
        #    self.stream.close()
        # get the time that this sequence started at and make it a TimeTuple
        t = self.rolloverAt - self.interval
        if self.utc:
            timeTuple = time.gmtime(t)
        else:
            timeTuple = time.localtime(t)
        dfn = self.baseFilename + "." + time.strftime(self.suffix, timeTuple)
        #if os.path.exists(dfn):
        #    os.remove(dfn)
        with filelock.FileLock("rotate_yueban_log.lock"):
            if not os.path.exists(dfn) and os.path.exists(self.baseFilename):
                os.rename(self.baseFilename, dfn)
                with open(self.baseFilename, 'a'):
                    pass
        if self.backupCount > 0:
            # find the oldest log file and delete it
            #s = glob.glob(self.baseFilename + ".20*")
            #if len(s) > self.backupCount:
            #    s.sort()
            #    os.remove(s[0])
            for s in self.getFilesToDelete():
                os.remove(s)
        #print "%s -> %s" % (self.baseFilename, dfn)
        if self.stream:
            self.stream.close()
        self.mode = 'a'
        self.stream = self._open()
        currentTime = int(time.time())
        newRolloverAt = self.computeRollover(currentTime)
        while newRolloverAt <= currentTime:
            newRolloverAt = newRolloverAt + self.interval
        #If DST changes and midnight or weekly rollover, adjust for this.
        if (self.when == 'MIDNIGHT' or self.when.startswith('W')) and not self.utc:
            dstNow = time.localtime(currentTime)[-1]
            dstAtRollover = time.localtime(newRolloverAt)[-1]
            if dstNow != dstAtRollover:
                if not dstNow:  # DST kicks in before next rollover, so we need to deduct an hour
                    newRolloverAt = newRolloverAt - 3600
                else:           # DST bows out before next rollover, so we need to add an hour
                    newRolloverAt = newRolloverAt + 3600
        self.rolloverAt = newRolloverAt


async def _yueban_handler(request):
    path = request.match_info['path']
    bs = await request.read()
    data = utility.loads(bs)
    if path == 'log':
        category, log_string = data
        logger_obj = get_logger(category)
        logger_obj.log(log_string)
        return web.Response(body=b'')
    elif path == 'stat':
        collection_name, documents = data
        conn = storage.get_stat_conn()
        await conn[collection_name].insert(documents)
        return web.Response(body=b'')
    else:
        return web.Response(body=b'')


def get_web_app():
    return _web_app


def start():
    global _logger
    global _web_app
    loop = asyncio.get_event_loop()
    loop.run_until_complete(initialize())
    _web_app = web.Application()
    _web_app.router.add_post('/yueban/{path}', _yueban_handler)