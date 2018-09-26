import time
from constants import EXCHANGE_ID
from itertools import chain
import asyncio
from random import random

def get_pairwise_key(pair):
    return f'TRADE:{EXCHANGE_ID}:{pair}'


class Trade:

    def __init__(self, trade_id, redis_pool):
        self.trade_id = int(trade_id)
        self.exchange_id = EXCHANGE_ID
        self.key = f'TRADEDETAIL:{self.exchange_id}:{self.trade_id}'
        self.redis_pool = redis_pool

    async def update(self, ask, bid, amount=None):
        print(self.key)
        if amount is None:
            amount = ask["amount"]
        async with self.redis_pool.get() as redis:
            val = await redis.execute('HKEYS', self.key)
            if val:
                await redis.execute('HINCRBYFLOAT', self.key, 'amount', amount)
            else:
                now = time.time()
                data = {
                    "price":ask["price"],
                    "pair": ask["pair"],
                    "amount":amount,
                    "bid_user":bid["userid"],
                    "ask_user":ask["userid"],
                    "server_time":now,
                    "trade_id": self.trade_id,
                }
                await redis.execute('HMSET', self.key, *chain.from_iterable(data.items()))

    async def as_dict(self):
        async with self.redis_pool.get() as redis:
            val = [i.decode() for i in await redis.execute('HGETALL', self.key)]
        return dict(zip(val[::2], val[1::2]))

    async def save_pairwise_data(self, data):
        pair = data['pair']
        key = get_pairwise_key(pair)
        async with self.redis_pool.get() as redis:
            await redis.execute('ZADD', key, data['server_time'], data['trade_id'])


async def get_pairwise_trades(pair, redis_pool):
    if random() < .02 :
        async with redis_pool.get() as redis:
            val = await redis.execute('ZCARD', get_pairwise_key(pair))
            if val > 20:
                print(f'cleaning up old trades {val}')
                await redis.execute('ZPOPMIN', get_pairwise_key(pair), val - 20)


    async with redis_pool.get() as redis:
        trade_ids = await redis.execute(
            'ZREVRANGE',
            get_pairwise_key(pair),
            -20,
            -1,
        )
    trade_coros = [Trade(int(t), redis_pool).as_dict() for t in trade_ids]
    return await asyncio.gather(*trade_coros)


