from constants import PAIRS
from decimal import Decimal


def price_to_score(side, price, pair):
    ticksize = PAIRS[pair]['ticksize']
    return str(Decimal(price) / Decimal(ticksize))


def orderbook_key_redis(exchange, pair, side):
    if side.lower() in ['bid', 'bids', 'buy']:
        return f'BIDS:exchange-{exchange}:{pair}'
    if side.lower() in ['ask', 'asks', 'sell']:
        return f'ASKS:exchange-{exchange}:{pair}'

def order_detail_key_redis(exchange_id, order_id):
    return f'ORDERDETAIL:{exchange_id}:{order_id}'


class RedisQueryEngine:

    def __init__(self, exchange):
        self.exchange = exchange

    def get_order_ids_by_price(self, pair, side, price):
        """
        Given a pair, side of order, and a price point return order ids
        """
        price_score = price_to_score(side, price, pair)
        return ('ZRANGEBYSCORE',
                orderbook_key_redis(self.exchange, pair, side),
                price_score,
                price_score,
        )

    def get_order_amount_by_order_id(self, order_id):
        return (
            'HGET',
            order_detail_key_redis(self.exchange, order_id),
            'amount'
        )
