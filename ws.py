import asyncio
from aioredis import create_connection, Channel
import json
import websockets
import time


async def subscribe_to_redis():
    conn = await create_connection(('localhost', 6379))
    channel = Channel('*', is_pattern=True)
    await conn.execute_pubsub('subscribe', channel)
    return channel, conn


async def redis_sub_handler(websocket):
    channel, conn = await subscribe_to_redis()
    while True:
        message = await channel.get()
        print(message)
        await websocket.send(message)


async def heartbeat():
    return {'OK':'OK'}


async def heartbeat_handler(websocket):
    while True:
        result = await heartbeat()
        await websocket.send(json.dumps(result))
        await asyncio.sleep(5)


async def websocket_handler(websocket, path):
    #heartbeat_task= asyncio.ensure_future(
    #    heartbeat_handler(websocket)
    #)
    redis_task = asyncio.ensure_future(
        redis_sub_handler(websocket)
    )

    done, pending = await asyncio.wait(
        [redis_task],
        return_when=asyncio.FIRST_COMPLETED,
    )
    for task in pending:
        task.cancel()

if __name__=='__main__':
    loop = asyncio.get_event_loop()
    loop.set_debug(True)
    loop.run_until_complete(
        websockets.serve(redis_sub_handler, 'localhost', 8765),
    )
    loop.run_forever()
