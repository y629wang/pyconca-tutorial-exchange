import asyncio
import config
import aioredis
from aioredis.pubsub import Receiver
import websockets
from config import HEARTBEAT_DURATION
from constants import EXCHANGE_ID
import json


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
            #self.redis_orders_ws_handler(websocket),
            self.heartbeat_ws_handler(websocket),
            self.redis_trades_ws_handler(websocket),
        )

    async def get_redis_connection(self):
        return await aioredis.create_connection((config.REDIS_PATH, 6379))

    async def redis_query(self, query, *args):
        conn = await self.get_redis_connection()
        return await conn.execute(query, *args, encoding='utf-8')

    async def redis_ping(self):
        conn = await self.get_redis_connection()
        return await self.redis_query('ping')

    async def get_order_state(self, order_delta):
        order_data = json.loads(message[1])
        side = order_data['side']
        price = order_data['price']
        pair = order_data['pair']
        order_id_query = self.query_maker.get_order_ids_by_price(pair,
                                                                 side,
                                                                 price)


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
        while True:
            await asyncio.sleep(HEARTBEAT_DURATION)
            # message = await self.redis_ping()
            message = str(await self.redis_query(
                'ZRANGEBYSCORE',
                'ASKS:exchange-1:ETHUSD',
                '192120000',
                '192120000',
            ))
            #await websocket.send('💚')
            await websocket.send(message)


if __name__ == '__main__':
    feed = RedisToWS()
    feed.start()
