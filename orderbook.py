from constants import EXCHANGE_ID, PAIRS
from exceptions import MalformedInputException
from itertools import chain


class Exchange:
    def __init__(self, redis_pool):
        self._redis_pool = redis_pool
        self._orderbooks = {p:Orderbook(p, redis_pool) for p in PAIRS}
        self._order_id_key = f'ORDERID:{EXCHANGE_ID}'

    async def reset_orderid_if_required(self):
        async with self._redis_pool.get() as redis:
            await redis.execute('SETNX', self._order_id_key, 1)

    async def get_incremented_order_id(self):
        async with self._redis_pool.get() as redis:
            val = await redis.execute('INCR', self._order_id_key)
        print(f'GET INCREMENTED ORDER ID {val}')
        return val

    def get_orderbook(self, pair):
        try:
            return self._orderbooks[pair]
        except KeyError:
            raise MalformedInputException(f'Unsupported Pair : {pair}')


class Orderbook:
    def __init__(self, pair, redis_pool):
        self.pair = pair
        self.redis_pool = redis_pool
        self._keys = {'bid': f'BIDS:exchange-{EXCHANGE_ID}:{pair}',
                      'ask': f'ASKS:exchange-{EXCHANGE_ID}:{pair}',
        }

    async def _insert_to_bid(self, order_id, price):
        async with self.redis_pool.get() as redis:
            print(self._keys['bid'])
            await redis.execute('ZADD', self._keys['bid'], price, order_id)

    async def _insert_to_ask(self, order_id, price):
        async with self.redis_pool.get() as redis:
            print(self._keys['ask'])
            await redis.execute('ZADD', self._keys['ask'], price, order_id)

    def _check_for_matches(self):
        pass

    async def _remove_from_bid_and_ask(self, order_id):
        async with self.redis_pool.get() as redis:
            a = await redis.execute('ZREM', self._keys['bid'], order_id)
            b = await redis.execute('ZREM', self._keys['ask'], order_id)
        return bool(a+b)

    def match_orders(self, buy_id, sell_id):
        """
        iteratively match orders, until no match
        """
        pass

    async def insert_order(self, order_id, pair, amount, price, side, userid):
        """
        order is a dict with keys : side (bid/ask)
                                    price
                                    amount
        """
        if side == 'bid':
            await self._insert_to_bid(order_id, price)
        else:
            await self._insert_to_ask(order_id, price)
        data = {'price':price, 'amount':amount, 'side':side, 'pair':pair, 'userid':userid}
        await OrderDetail(order_id).set_data(data, self.redis_pool)
        return data

    async def remove_order(self, order_id):
        """
        cancel order with given id
        """
        found = await self._remove_from_bid_and_ask(order_id)
        await OrderDetail(order_id).pop(self.redis_pool)
        return found

    async def get_orders(self):
        """
        returns all orders in the orderbook right now. paginated by 20
        """
        async with self.redis_pool.get() as redis:
            asks = await redis.execute('ZRANGE', self._keys['ask'], 0, 20)
            bids = await redis.execute('ZREVRANGE', self._keys['bid'], 0, 20)
        return ([await OrderDetail(b).get_data(self.redis_pool) for b in bids],
               [await OrderDetail(a).get_data(self.redis_pool) for a in asks])


class OrderDetail:
    def __init__(self, order_id):
        self.order_id = int(order_id)
        self.exchange_id = EXCHANGE_ID
        self.key = f'ORDERDETAIL:{self.exchange_id}:{self.order_id}'

    async def set_data(self, data, redis_pool):
        async with redis_pool.get() as redis:
            await redis.execute(
                'HMSET',
                self.key,
                *chain.from_iterable(data.items()),
            )

    async def pop(self, redis_pool):
        async with redis_pool.get() as redis:
            await redis.execute('DEL', self.key)

    async def get_data(self, redis_pool):
        decoder = lambda x: x.decode() # bytes to string
        async with redis_pool.get() as redis:
            val = [i.decode() for i in await redis.execute('HGETALL', self.key)]
            return {**dict(zip(val[::2], val[1::2])), 'orderid':self.order_id}
