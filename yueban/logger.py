"""
Service-collect logs:
"""

import logging
import logging.handlers
import os
import os.path
import time
from logging.handlers import TimedRotatingFileHandler
from aiohttp import web
from . import utility


_web_app = None
_loggers = {}


def _ensure_logger(category, log_name='yueban.log'):
    global _loggers
    _logger = logging.getLogger('')
    _logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s %(message)s")
    if not os.path.exists(category):
        os.makedirs(category)
    path = os.path.join(category, log_name)
    handler = MultiProcessTimedRotatingFileHandler(path, when="MIDNIGHT")
    handler.suffix = "%Y%m%d"
    handler.setFormatter(formatter)
    _logger.addHandler(handler)
    _loggers[category] = _logger


def get_logger(category):
    _ensure_logger(category)
    return _loggers[category]


class MultiProcessTimedRotatingFileHandler(TimedRotatingFileHandler):
    """
    MultiProcess with a same log-file
    """
    def doRollover(self):
        """
        do a rollover; in this case, a date/time stamp is appended to the
        filename when the rollover happens.  However, you want the file to
        be named for the start of the interval, not the current time.
        If there is a backup count, then we have to get a list of matching
        filenames, sort them and remove the one with the oldest suffix.
        """
        if self.stream:
            self.stream.close()
        # get the time that this sequence started at and make it a TimeTuple
        t = self.rolloverAt - self.interval
        if self.utc:
            timeTuple = time.gmtime(t)
        else:
            timeTuple = time.localtime(t)
        dfn = self.baseFilename + "." + time.strftime(self.suffix, timeTuple)
        if not os.path.exists(dfn):
            os.rename(self.baseFilename, dfn)
        if self.backupCount > 0:
            # find the oldest log file and delete it
            for s in self.getFilesToDelete():
                os.remove(s)
        self.mode = 'a'
        self.stream = self._open()
        currentTime = int(time.time())
        newRolloverAt = self.computeRollover(currentTime)
        while newRolloverAt <= currentTime:
            newRolloverAt = newRolloverAt + self.interval
        #If DST changes and midnight or weekly rollover, adjust for this.
        if (self.when == 'MIDNIGHT' or self.when.startswith('W'))\
                and not self.utc:
            dstNow = time.localtime(currentTime)[-1]
            dstAtRollover = time.localtime(newRolloverAt)[-1]
            if dstNow != dstAtRollover:
             # DST kicks in before next rollover, so we need to deduct an hour
                if not dstNow:
                    newRolloverAt = newRolloverAt - 3600
             # DST bows out before next rollover, so we need to add an hour
                else:
                    newRolloverAt = newRolloverAt + 3600
        self.rolloverAt = newRolloverAt


async def _yueban_handler(request):
    path = request.path
    bs = await request.read()
    data = utility.loads(bs)
    if path == '/yueban/log':
        category, log_string = data
        logger_obj = get_logger(category)
        logger_obj.info(log_string)
        return utility.pack_pickle_response('')
    else:
        utility.print_out('bad_logger_handler', path, data)
        return utility.pack_pickle_response('')


def get_web_app():
    return _web_app


def start():
    global _web_app
    _web_app = web.Application()
    _web_app.router.add_post('/yueban/{path}', _yueban_handler)
