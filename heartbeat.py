import asyncio
import websockets


class HeartBeatWS:

    def __init__(self):
        self.loop = asyncio.get_event_loop()
        self.loop.set_debug(True)
        # print('heartbeat starting up')
        # print('return_when=asyncio.FIRST_COMPLETED')

    def start(self):
        self.loop.run_until_complete(
            websockets.serve(self.ws_handler, '0.0.0.0', 9999),
        )
        self.loop.run_forever()

    async def ws_handler(self, websocket, path):

    async def beat1(self):
        while True:
            await asyncio.sleep(0.9)
            await websocket.send('💚')

    async def beat2(self):
        while True:
            await asyncio.sleep(3)
            await websocket.send('💜')


if __name__ == '__main__':
    HeartBeatWS().start()


