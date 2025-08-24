from xtquant import xtdata
import time

def get_last_price(stock):
    full_tick = xtdata.get_full_tick([stock])
    # print(f"{stock} 全推行情： {full_tick}")
    current_price = full_tick[stock]['lastPrice']
    return current_price
