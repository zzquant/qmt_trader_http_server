# coding=utf-8


def get_stock_type(stock_code):
    """判断股票ID对应的证券市场
    匹配规则
    ['50', '51', '60', '90', '110'] 为 sh
    ['00', '13', '18', '15', '16', '18', '20', '30', '39', '115'] 为 sz
    ['5', '6', '9'] 开头的为 sh， 其余为 sz
    :param stock_code:股票ID, 若以 'sz', 'sh' 开头直接返回对应类型，否则使用内置规则判断
    :return 'sh' or 'sz'"""
    stock_code = str(stock_code)
    if stock_code.startswith(('sh', 'sz')):
        return stock_code[:2]
    if stock_code.startswith(('50', '51', '60', '73', '90', '110', '113', '132', '204', '78')):
        return 'sh'
    if stock_code.startswith(('00', '12', '13', '18', '15', '16', '18', '20', '30', '39', '115', '1318')):
        return 'sz'
    if stock_code.startswith(('5', '6')):
        return 'sh'
    if stock_code.startswith(('8', '4', '9')):
        return 'bj'
    return 'sz'

def get_stock_id_hson_helpers(stock_code):
    code = stock_code
    idx = stock_code.find('.')
    if idx > 0:
        code = code[0:idx]
    # suffix = ".SS" if get_stock_type(stock_code) == 'sh' else ".SZ"
    suffix = (
        ".BJ" if get_stock_type(stock_code) == 'bj'
        else ".SS" if get_stock_type(stock_code) == 'sh'
        else ".SZ"
    )
    code = str(code) + suffix
    return code


def get_stock_id_xt(stock_code):
    code = stock_code
    idx = stock_code.find('.')
    if idx > 0:
        code = code[0:idx]
    # suffix = ".SS" if get_stock_type(stock_code) == 'sh' else ".SZ"
    suffix = (
        ".BJ" if get_stock_type(stock_code) == 'bj'
        else ".SH" if get_stock_type(stock_code) == 'sh'
        else ".SZ"
    )
    code = str(code) + suffix
    return code


def get_stock_id_hson(stock_code):
    """
    转换成股票代码id,600136.XSHG->6001361
    """
    """判断股票ID对应的证券市场
    匹配规则
    ['50', '51', '60', '90', '110'] 为 sh
    ['00', '13', '18', '15', '16', '18', '20', '30', '39', '115'] 为 sz
    ['5', '6', '9'] 开头的为 sh， 其余为 sz
    :param stock_code:股票ID, 若以 'sz', 'sh' 开头直接返回对应类型，否则使用内置规则判断
    :return 'sh' or 'sz'"""
    code = stock_code
    idx = stock_code.find('.')
    if idx > 0:
        code = code[0:idx]
    suffix = ".SS" if get_stock_type(stock_code) == 'sh' else ".SZ"
    code = str(code) + suffix
    return code


def get_stock_id_jq(stock_code):
    code = stock_code
    idx = stock_code.find('.')
    if idx > 0:
        code = code[0:idx]
    suffix = ".XSHG" if get_stock_type(stock_code) == 'sh' else ".XSHE"
    code = str(code) + suffix
    return code


def get_high_low_limit(symbol_code, preclose_px):
    """
    计算涨跌停价格
    """
    if symbol_code.startswith("300") or symbol_code.startswith("688"):
        return round(preclose_px * 1.2, 2), round(preclose_px * 0.8, 2)
    return round(preclose_px * 1.1, 2), round(preclose_px * 0.9, 2)


#计算当前时间距离开盘时间的分钟数
def open_time_delta(dt):
    hour = dt.hour
    minute = dt.minute
    if hour == 9:
        return minute-30
    if hour == 10:
        return 30+minute
    if hour == 11:
        return 90+minute
    if hour == 13:
        return 120+minute
    if hour == 14:
        return 180+minute
    if hour == 15:
        return 240
    return 240

