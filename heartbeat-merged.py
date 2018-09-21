import asyncio
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
        first_beat = asyncio.ensure_future(
            self.beat1(websocket),
        )
        second_beat = asyncio.ensure_future(
            self.beat2(websocket),
        )

        done, pending = await asyncio.wait(
            [first_beat, second_beat],
            return_when=asyncio.FIRST_COMPLETED,
        )

    async def beat1(self, websocket):
        while True:
            await asyncio.sleep(0.8)
            await websocket.send('💚')

    async def beat2(self, websocket):
        while True:
            await asyncio.sleep(1.1)
            await websocket.send('💓')



if __name__ == '__main__':
    HeartBeatWS().start()
