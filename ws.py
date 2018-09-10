import asyncio
import json
import websockets
import time
from collections import namedtuple


ActiveTask = namedtuple('ActiveTask', ['method', 'sleep_duration', 'name'])

async def heartbeat():
    return {'OK':'OK'}


async def heartbeat_handler(websocket):
    while True:
        result = await heartbeat()
        await websocket.send(json.dumps(result))
        await asyncio.sleep(5)


async def websocket_handler(websocket, path):
    heartbeat_task= asyncio.ensure_future(
        heartbeat_handler(websocket)
    )
    done, pending = await asyncio.wait(
        [heartbeat_task],
        return_when=asyncio.FIRST_COMPLETED,
    )
    for task in pending:
        task.cancel()


asyncio.get_event_loop().run_until_complete(
    websockets.serve(websocket_handler, 'localhost', 8765),
)

asyncio.get_event_loop().run_forever()
