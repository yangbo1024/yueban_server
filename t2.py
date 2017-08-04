

import asyncio
import aiohttp

async def http_get(url):
    async with aiohttp.ClientSession() as session:
         async with session.get(url) as resp:
             return resp.status, await resp.read()


ret = asyncio.get_event_loop().run_until_complete(http_get('http://www.baidu.com'))
t = ret[1]
print(t)
