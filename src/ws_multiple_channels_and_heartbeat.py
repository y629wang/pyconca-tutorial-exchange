import asyncio
import config
import aioredis
from aioredis.pubsub import Receiver
import websockets
from config import HEARTBEAT_DURATION


class RedisToWS:

    def __init__(self):
        self.loop = asyncio.get_event_loop()
        self.loop.set_debug(True)
        self.channel = 'updates'

    def start(self):
        self.loop.run_until_complete(
            websockets.serve(self.ws_handler, '0.0.0.0', 8765),
        )
        self.loop.run_forever()

    async def ws_handler(self, websocket, path):
        # gather redis_ws_handler and heartbeat_ws_heandler
        await asyncio.gather(
            self.redis_ws_handler(websocket),
            self.heartbeat_ws_handler(websocket),
            self.redis_trades_ws_handler(websocket),
        )

    async def redis_ws_handler(self, websocket):
        print('receive starting from redis')
        connection = await aioredis.create_connection((config.REDIS_PATH, 6379))
        receiver = Receiver()
        connection.execute_pubsub('subscribe', receiver.channel(self.channel))
        while (await receiver.wait_message()):
            message = await receiver.get()
            await websocket.send(self.parse_redis_message(message))

    async def redis_trades_ws_handler(self, websocket):
        connection = await aioredis.create_connection((config.REDIS_PATH, 6379))
        receiver = Receiver()
        connection.execute_pubsub('subscribe', receiver.channel('trades'))
        while (await receiver.wait_message()):
            message = await receiver.get()
            await websocket.send(self.parse_redis_message(message))

    async def heartbeat_ws_handler(self, websocket):
        while True:
            await asyncio.sleep(HEARTBEAT_DURATION)
            await websocket.send('💚')

    def parse_redis_message(self, message):
        return message[1].decode('utf-8')


if __name__ == '__main__':
    feed = RedisToWS()
    feed.start()
