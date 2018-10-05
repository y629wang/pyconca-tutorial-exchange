from constants import PAIRS


def price_to_score(side, price, pair)
    ticksize = PAIRS[pair]['ticksize']
    price_score = str(Decimal(price) / Decimal(ticksize))
