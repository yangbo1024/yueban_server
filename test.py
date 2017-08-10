
import sys


sys.path.append('./yueban')

import asyncio
import yueban
from yueban import gater
from yueban import worker


cfg = {
    'cache_redis': {
        'host': '10.0.30.26',
        'port': 20100,
        'password': 'yj123456789.',
        'db': 0,
    },
    'schedule_redis': {
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
}


loop = asyncio.get_event_loop()
loop.run_until_complete(yueban.initialize(cfg))


class Worker(worker.GameWorker):
    async def on_call(self, request):
        print('on call', request.match_info)

    async def on_client_closed(self, client_id):
       pass

    async def on_proto(self, proto_id, proto_body):
        pass


print('app name', __name__)
worker.start(Worker())
worker_app = worker.get_app()



