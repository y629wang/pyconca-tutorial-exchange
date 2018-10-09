from constants import EXCHANGE_ID, PAIRS
from common import price_to_score
import time
import asyncio
from exceptions import MalformedInputException
from itertools import chain
import json
from decimal import Decimal
from trades import Trade


class Exchange:
    def __init__(self, redis_pool):
        self.redis_pool = redis_pool
        self._orderbooks = {p:Orderbook(p, redis_pool) for p in PAIRS}
        self._order_id_key = f'ORDERID:{EXCHANGE_ID}'
        self._trade_id_key = f'TRADEID:{EXCHANGE_ID}'

    async def reset_orderid_if_required(self):
        async with self.redis_pool.get() as redis:
            await redis.execute('SETNX', self._order_id_key, 1)
            await redis.execute('SETNX', self._trade_id_key, 1)

    async def get_incremented_order_id(self):
        async with self.redis_pool.get() as redis:
            val = await redis.execute('INCR', self._order_id_key)
        return val

    async def get_incremented_trade_id(self):
        async with self.redis_pool.get() as redis:
            val = await redis.execute('INCR', self._trade_id_key)
        return val

    async def get_latest_trades(self):
        async with self.redis_pool.get() as redis:
            latest_trade_id = int(await redis.execute('GET', self._trade_id_key))
            relevant_trade_ids = range(
                latest_trade_id,
                max(latest_trade_id - 20, 0),
                -1,
            )
            trades_coro = [Trade(i,self.redis_pool).as_dict() for i in relevant_trade_ids]
            trades = await asyncio.gather(*trades_coro)
        return trades

    def get_orderbook(self, pair):
        try:
            return self._orderbooks[pair]
        except KeyError:
            raise MalformedInputException(f'Unsupported Pair : {pair}')


class Orderbook:
    def __init__(self, pair, redis_pool):
        self.pair = pair
        self.redis_pool = redis_pool
        self._keys = lambda side: orderbook_key_redis(EXCHANGE_ID, pair, side)

    async def _insert_to_bid(self, order_id, price):
        async with self.redis_pool.get() as redis:
            print(self._keys('bid'))
            await redis.execute('ZADD', self._keys('bid'), '-' + price, order_id)

    async def publish_message(self, message, channel):
        async with self.redis_pool.get() as redis:
            await redis.execute('PUBLISH', channel, message)

    async def _insert_to_ask(self, order_id, price):
        async with self.redis_pool.get() as redis:
            print(self._keys('ask'))
            await redis.execute('ZADD', self._keys('ask'), price, order_id)

    async def check_for_matches(self):
        try:
            top_bid, top_ask = await self._get_top_of_book()
        except IndexError:
            return False
        return Decimal(top_bid['price']) >= Decimal(top_ask['price'])

    async def _get_top_of_book(self):
        bids, asks = await self.get_orders(n=1)
        return bids[0], asks[0]

    async def _matching_engine(self, trade):
        try:
            top_bid, top_ask = await self._get_top_of_book()
        except IndexError:
            return False
        if Decimal(top_bid['price']) < Decimal(top_ask['price']):
            return False

        # if it matches fully remove the orders
        if Decimal(top_bid['amount']) == Decimal(top_ask['amount']):
            aaa = await self.remove_order(top_ask['orderid'])
            # remove the bid
            bbb = await self.remove_order(top_bid['orderid'])
            await trade.update(top_ask, top_bid)
            return True

        # if it matches partually, remove an order and modify the other one
        if Decimal(top_bid['amount']) > Decimal(top_ask['amount']):
            #trade = self._make_trade(top_bid, top_ask, amount=top_ask['amount'])
            await self.remove_order(top_ask['orderid'])
            await self._reduce_order(
                top_bid['orderid'],
                amount=top_ask['amount'],
            )
            await trade.update(top_ask, top_bid, top_ask['amount'])
            return True

        if Decimal(top_bid['amount']) < Decimal(top_ask['amount']):
            #trade = self._make_trade(top_bid, top_ask, amount=top_bid['amount'])
            await self.remove_order(top_bid['orderid'])
            await self._reduce_order(
                top_ask['orderid'],
                amount=top_bid['amount'],
            )
            await trade.update(top_ask, top_bid, top_bid['amount'])
            return True

    async def _reduce_order(self, order_id, amount):
        await OrderDetail(order_id).reduce_amount(amount, self.redis_pool)

    async def _remove_from_bid_and_ask(self, order_id):
        async with self.redis_pool.get() as redis:
            a = await redis.execute('ZREM', self._keys('bid'), order_id)
            b = await redis.execute('ZREM', self._keys('ask'), order_id)
        return bool(a+b)

    async def run_order_matching_engine(self, trade_id):
        trade = Trade(trade_id, self.redis_pool)
        need_matching = True
        while need_matching:
            need_matching = await self._matching_engine(trade)
        trade_data = await trade.as_dict()
        await self.publish_message(json.dumps(trade_data), 'trades')
        await trade.save_pairwise_data(trade_data)

    async def insert_order(self, order_id, pair, amount, price, side, userid):
        price_score = price_to_score(side, price, pair)
        if side == 'bid':
            await self._insert_to_bid(order_id, price_score)
        else:
            await self._insert_to_ask(order_id, price_score)
        data = {'price':price, 'amount':amount, 'side':side, 'pair':pair, 'userid':userid}
        data = await OrderDetail(order_id).set_data(data, self.redis_pool)
        await self.publish_message(json.dumps(data), 'orders')
        return data

    async def remove_order(self, order_id):
        """
        cancel order with given id
        """
        found = await self._remove_from_bid_and_ask(order_id)
        if found:
            data = await OrderDetail(order_id).pop(self.redis_pool)
            data['amount'] = '-' + data['amount']
            await self.publish_message(json.dumps(data), 'orders')
        return found

    async def get_orders(self, n=20):
        """
        returns all orders in the orderbook right now. paginated by 20
        """
        async with self.redis_pool.get() as redis:
            asks = await redis.execute('ZRANGE', self._keys('ask'), 0, n-1)
            bids = await redis.execute('ZRANGE', self._keys('bid'), 0, n-1)
        return ([await OrderDetail(b).get_data(self.redis_pool) for b in bids],
               [await OrderDetail(a).get_data(self.redis_pool) for a in asks])


class OrderDetail:
    def __init__(self, order_id):
        self.order_id = int(order_id)
        self.exchange_id = EXCHANGE_ID
        self.key = f'ORDERDETAIL:{self.exchange_id}:{self.order_id}'

    async def reduce_amount(self, amount, redis_pool):
        async with redis_pool.get() as redis:
            await redis.execute('HINCRBYFLOAT', self.key, 'amount', '-' + amount)

    async def set_data(self, data, redis_pool):
        async with redis_pool.get() as redis:
            await redis.execute(
                'HMSET',
                self.key,
                *chain.from_iterable(data.items()),
            )
        return await self.get_data(redis_pool)

    async def pop(self, redis_pool):
        async with redis_pool.get() as redis:
            data = await self.get_data(redis_pool)
            await redis.execute('DEL', self.key)
        return data

    async def get_data(self, redis_pool):
        async with redis_pool.get() as redis:
            val = [i.decode() for i in await redis.execute('HGETALL', self.key)]
        return {**dict(zip(val[::2], val[1::2])), 'orderid':self.order_id}
