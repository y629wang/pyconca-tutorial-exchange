import asyncio
import aioredis
from aioredis.pubsub import Receiver
import websockets


class HeartBeatWS:

    def __init__(self):
        self.loop = asyncio.get_event_loop()
        self.loop.set_debug(True)

    def start(self):
        self.loop.run_until_complete(
            websockets.serve(self.ws_handler, '0.0.0.0', 9999),
        )
        self.loop.run_forever()

    async def ws_handler(self, websocket, path):
        print('heartbeat starting')
        while True:
            await asyncio.sleep(2)
            await websocket.send('❤')



if __name__ == '__main__':
    HeartBeatWS().start()
