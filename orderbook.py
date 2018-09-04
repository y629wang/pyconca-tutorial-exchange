from constants import EXCHANGE_ID, PAIRS
from exceptions import MalformedInputException


class Exchange:

    def __init__(self, redis_pool):
        self._orderbooks = {p:Orderbook(p) for p in PAIRS}
        self._redis_pool = redis_pool
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

    def __init__(self, pair):
        self.pair = pair
        self._keys = {'bid': f'BIDS:{EXCHANGE_ID}:{pair}',
                      'ask': f'ASKS:{EXCHANGE_ID}:{pair}',
                      'data': f'ORDERS:{EXCHANGE_ID}:{pair}',
        }

    def _insert_to_bid(self, order):
        pass

    def _insert_to_ask(self, order):
        pass

    def _insert_order_details(self, order):
        pass

    def _check_for_matches(self):
        pass

    def _remove_from_bid(self):
        pass

    def _remove_from_ask(self):
        pass

    def _remove_order_details(self):
        pass

    def _generate_order_id(self):
        pass

    def match_orders(self, buy_id, sell_id):
        """
        iteratively match orders, until no match
        """
        pass

    def insert_order(self, order):
        """
        order is a dict with keys : side (bid/ask)
                                    price
                                    amount
        """
        pass

    def remove_order(self, order_id):
        """
        cancel order with given id
        """
        pass
