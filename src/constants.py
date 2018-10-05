from collections import namedtuple
from os import environ


BALANCES = {
    'USD': '100',
    'BTC': '0.2',
    'ETH': '1.9',
    'XLM': '197',
}
EXCHANGE_ID = int(environ.get('EXCHANGE_ID', 1))
PAIRS_DATA = {1: {'ETHUSD':{'ticksize':'0.0000001','quantity_increment':'0.001'},
                  'ETHBTC':{'ticksize':'0.00000001','quantity_increment':'0.001'},
                  'BTCUSD':{'ticksize':'0.00000001','quantity_increment':'0.001'},
                  'XLMBTC':{'ticksize':'0.000001','quantity_increment':'0.001'},
                 },
              2: {'ETHUSD':{'ticksize':'0.0000001','quantity_increment':'0.001'},
                  'ETHBTC':{'ticksize':'0.00000001','quantity_increment':'0.001'},
                  'BTCUSD':{'ticksize':'0.00000001','quantity_increment':'0.001'},
                  'XLMETH':{'ticksize':'0.000001','quantity_increment':'0.001'},
                  'BCHBTC':{'ticksize':'0.000001','quantity_increment':'0.001'},
                 },
              3: {'BCHUSD':{'ticksize':'0.0000001','quantity_increment':'0.001'},
                  'ETHBTC':{'ticksize':'0.00000001','quantity_increment':'0.001'},
                  'BCHBTC':{'ticksize':'0.00000001','quantity_increment':'0.001'},
                  'XLMUSD':{'ticksize':'0.000001','quantity_increment':'0.001'},
                  'BCHETH':{'ticksize':'0.000001','quantity_increment':'0.001'},
                 },
            }

PAIRS = PAIRS_DATA[EXCHANGE_ID]
