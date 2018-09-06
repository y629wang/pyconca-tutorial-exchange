from sanic import Sanic
import time
from sanic.response import json
import aioredis
from constants import BALANCES, PAIRS
from orderbook import Exchange
from controllers import (
    place_order_controller,
    cancel_order_controller,
    get_orders_controller,
)
app = Sanic()


@app.route('/ping/')
async def ping(request):
    async with request.app.redis_pool.get() as redis:
        now = int(time.time())
        await redis.execute('SET','test-ping-key', f'PONG at {now}')
        val = await redis.execute('GET','test-ping-key', encoding='utf-8')
    return json({'ping':val})


@app.post('/orders/', name='place_order')
async def place_order(request):
    """
    pair, amount, price, side in the input
    side: bid / ask
    """
    response = await place_order_controller(request.json, request.app.exchange)
    return response


@app.delete('/orders/', name='cancel_order')
async def cancel_order(request):
    """
    order_id, pair in input
    """
    response = await cancel_order_controller(request.json, request.app.exchange)
    return response


@app.get('/orders/', name='list_orders_page')
async def list_orders_page(request):
    response = await get_orders_controller(request.args, request.app.exchange)
    # convert data to html via jinja
    return response


@app.get('/pairs/', name='list_pairs')
async def list_pairs(request):
    return json(PAIRS)


@app.get('/balance/', name='user_balance')
async def user_balance(request):
    return json(BALANCES)


@app.listener('before_server_start')
async def before_server_start(app, loop):
    app.redis_pool = await aioredis.create_pool(
        ('localhost', 6379),
        minsize=5,
        maxsize=10,
        loop=loop
    )
    app.exchange = Exchange(app.redis_pool)
    await app.exchange.reset_orderid_if_required()


@app.listener('after_server_stop')
async def after_server_stop(app, loop):
    app.redis_pool.close()
    await app.redis_pool.wait_closed()


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000)
