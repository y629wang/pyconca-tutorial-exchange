from sanic import Sanic
import time
from sanic.response import json
import aioredis

app = Sanic()


@app.route('/ping/')
async def ping(request):
    async with request.app.redis_pool.get() as redis:
        now = int(time.time())
        await redis.execute('set','test-ping-key', f'PONG at {now}')
        val = await redis.execute('get','test-ping-key', encoding='utf-8')
    return json({'ping':val})


@app.listener('before_server_start')
async def before_server_start(app, loop):
    app.redis_pool = await aioredis.create_pool(
        ('localhost', 6379),
        minsize=5,
        maxsize=10,
        loop=loop
    )


@app.listener('after_server_stop')
async def after_server_stop(app, loop):
    app.redis_pool.close()
    await app.redis_pool.wait_closed()


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000)
