from sanic import response
from exceptions import MalformedInputException


async def place_order_controller(data, exchange):
    try:
        orderbook = exchange.get_orderbook(data['pair'])
    except MalformedInputException as e:
        return response.json(
            {'error':'unrecognized pair', 'request_params': data},
            status=422,
        )
    except KeyError:
        return response.json(
            {'error':'Bad input, pair not found', 'request_params': data},
            status=400,
        )
    order_id = await exchange.get_incremented_order_id()
    await orderbook.insert_order(order_id, data)
    return order_id


async def cancel_order_controller(data, exchange):
    pass
