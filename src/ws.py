import asyncio
import config
import aioredis
from aioredis.pubsub import Receiver
import websockets
from config import HEARTBEAT_DURATION, HEARBEAT_ON, DB_PING
from constants import EXCHANGE_ID
import json
from common import RedisQueryEngine
from decimal import Decimal


class RedisToWS:

    def __init__(self):
        self.loop = asyncio.get_event_loop()
        self.loop.set_debug(True)
        self.query_maker = RedisQueryEngine(EXCHANGE_ID)

    def start(self):
        self.loop.run_until_complete(
            websockets.serve(self.ws_handler, '0.0.0.0', 8765),
        )
        self.loop.run_forever()

    async def ws_handler(self, websocket, path):
        # gather redis_ws_handler and heartbeat_ws_heandler
        await asyncio.gather(
            self.redis_ping(websocket),
            self.redis_orders_ws_handler(websocket),
            self.heartbeat_ws_handler(websocket),
            self.redis_trades_ws_handler(websocket),
        )

    async def get_redis_connection(self):
        return await aioredis.create_connection((config.REDIS_PATH, 6379))

    async def redis_query(self, query, *query_args):
        if DB_PING:
            conn = await self.get_redis_connection()
            return await conn.execute(query, *query_args, encoding='utf-8')

    async def redis_ping(self, websocket):
        conn = await self.get_redis_connection()
        res = await self.redis_query('ping')
        await websocket.send(res)

    async def get_order_state(self, message):
        order_data = json.loads(message[1])
        side = order_data['side']
        price = order_data['price']
        pair = order_data['pair']
        userid = order_data['userid']
        query = self.query_maker.get_order_ids_by_price(pair, side, price)
        conn = await self.get_redis_connection()
        order_ids = await self.redis_query(*query)
        # this order_ids is the list of all orderids at this price, should contain just one item if no other order
        # if nothing is there that means it got matched and no amount (zero) is th latest state
        if order_ids:
            queries = [self.query_maker.get_order_amount_by_order_id(i) for i in order_ids]
            amounts = [await self.redis_query(*q) for q in queries]
            amount = str(sum(Decimal(i) for i in amounts))
        else:
            amount = '0'
        orders_state = {'price':price, 'side':side, 'amount':amount, 'userid':userid, 'n_orders':len(order_ids)}
        return str(orders_state)

    async def redis_orders_ws_handler(self, websocket):
        connection = await self.get_redis_connection()
        receiver = Receiver()
        connection.execute_pubsub('subscribe', receiver.channel('orders'))
        while (await receiver.wait_message()):
            order_delta = await receiver.get()
            actual_order = await self.get_order_state(order_delta)
            await websocket.send(actual_order)

    async def redis_trades_ws_handler(self, websocket):
        receiver = Receiver()
        connection = await self.get_redis_connection()
        connection.execute_pubsub('subscribe', receiver.channel('trades'))
        while (await receiver.wait_message()):
            message = await receiver.get()
            await websocket.send(message[1].decode('utf-8'))

    async def heartbeat_ws_handler(self, websocket):
        while HEARBEAT_ON:
            await asyncio.sleep(HEARTBEAT_DURATION)
            #message = str(await self.redis_query(
            #    'ZRANGEBYSCORE',
            #    'ASKS:exchange-1:ETHUSD',
            #    '192120000',
            #    '192120000',
            #))
            await websocket.send('💚')
            #await websocket.send(message)


if __name__ == '__main__':
    feed = RedisToWS()
    feed.start()
