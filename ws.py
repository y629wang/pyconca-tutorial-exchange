import asyncio
import aioredis
from aioredis.pubsub import Receiver
import websockets


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
        async for message in self.receive():
            print(message)
            await websocket.send(
                self.parse_message(message),
            )

    async def receive(self):
        print('receive starting from redis')
        connection = await aioredis.create_connection(('redis', 6379))
        receiver = Receiver()
        connection.execute_pubsub('subscribe', receiver.channel(self.channel))
        while (await receiver.wait_message()):
            message = await receiver.get()
            yield message[1].decode('utf-8')

    def parse_message(self, msg):
        return msg


if __name__ == '__main__':
    feed = RedisToWS()
    feed.start()
