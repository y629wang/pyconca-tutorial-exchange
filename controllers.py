from sanic import response
from exceptions import MalformedInputException
from constants import PAIRS
from decimal import Decimal
from jinja2 import Template


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
    pair_metadata = PAIRS[data['pair']]
    try:
        amount = str(Decimal(data['amount']).quantize(
            Decimal(pair_metadata['quantity_increment']),
        ))
    except:
        return response.json(
            {'error':'Bad input, amount parameter has some problems',
             'request_params': data,
            },
            status=400,
        )
    try:
        price = str(Decimal(data['price']).quantize(
            Decimal(pair_metadata['ticksize']),
        ))
    except:
        return response.json(
            {'error':'Bad input, price parameter has some problems',
             'request_params': data,
            },
            status=400,
        )
    side = data.get('side', '').lower()
    if side not in ['bid', 'ask']:
        return response.json(
            {'error':'Bad input, side should be either bid or ask',
             'request_params': data,
            },
            status=400,
        )
    try:
        userid = int(data['user_id'])
    except KeyError:
        return response.json(
            {'error':'Bad input, user_id not given',
             'request_params': data,
            },
            status=400,
        )
    except ValueError:
        return response.json(
            {'error':'Bad input, user_id should be an integer',
             'request_params': data,
            },
            status=400,
        )

    order_id = await exchange.get_incremented_order_id()
    details = await orderbook.insert_order(order_id, data['pair'], amount,
                                           price, side, userid)
    return response.json({'order_id': order_id, 'data':details})


async def cancel_order_controller(data, exchange):
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

    result = await orderbook.remove_order(data['order_id'])
    status = 200 if result else 422
    return response.json({}, status=status)


async def get_orders_controller(data, exchange):
    try:
        orderbook = exchange.get_orderbook(data['pair'][0])
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

    bids, asks = await orderbook.get_orders()
    with open('templates/orderbook.html.j2') as f:
        template_text = f.read()
    template = Template(template_text)
    return response.html(template.render(bids=bids, asks=asks))
