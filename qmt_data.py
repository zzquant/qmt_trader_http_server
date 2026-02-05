from doctest import FAIL_FAST
from math import fabs
from xtquant import xtdata
import time

def get_last_price(stock):
    full_tick = xtdata.get_full_tick([stock])
    # print(f"{stock} 全推行情： {full_tick}")
    current_price = full_tick[stock]['lastPrice']
    return current_price


def get_instrument_detail(stock_code, iscomplete=False):
    return xtdata.get_instrument_detail(stock_code, iscomplete)

def subscribe(stock_code):
    xtdata.subscribe_quote(stock_code, callback=f)

def f(data):
    print(data)
    now = datetime.datetime.now()
    for stock in data:
        cuurent_price = data[stock][0]['close']
        pre_price = data[stock][0]['preClose']
        ratio = cuurent_price / pre_price - 1 if pre_price > 0 else 0
        print(f"{now}  {stock}  最新价{cuurent_price} 涨幅 {ratio:.2%}")
        # if ratio > 0.09 and stock not in A.bought_list:
            
            # async_seq = xt_trader.order_stock_async(acc, stock, xtconstant.STOCK_BUY, 100, xtconstant.LATEST_PRICE, -1,
            #                                         'strategy_name', stock)
            # A.bought_list.append(stock)