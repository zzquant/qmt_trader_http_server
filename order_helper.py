# -*- coding: utf-8 -*-
import hmac
import hashlib
import time
import json

import requests


def generate_signature(method, path, query_string, body, timestamp, client_id, secret_key):
    """生成HMAC-SHA256签名"""
    # 构建签名字符串
    sign_string = f"{method}\n{path}\n{query_string}\n{body}\n{timestamp}\n{client_id}"

    # 计算HMAC-SHA256签名
    signature = hmac.new(
        secret_key.encode('utf-8'),
        sign_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    return signature


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


class PrivateQMTOrderHelper:
    def __init__(self, base_url, client_id, secret_key, trader_index=0, strategy_name="策略1"):
        self.base_url = base_url
        self.client_id = client_id
        self.secret_key = secret_key
        self.trader_index = trader_index
        self.strategy_name = strategy_name

    def _post(self, path, data, query_string=""):
        body = json.dumps(data, sort_keys=True, separators=(',', ':'))
        # 生成时间戳
        timestamp = str(int(time.time()))
        query_string = query_string

        # 生成签名
        signature = generate_signature('POST', path, query_string, body, timestamp, self.client_id, self.secret_key)

        # 构建请求头
        headers = {
            'Content-Type': 'application/json',
            'X-Client-ID': self.client_id,
            'X-Timestamp': timestamp,
            'X-Signature': signature
        }
        response = requests.post(f"{self.base_url}{path}", headers=headers, json=data)
        return response.json()

    def call_trade(self, symbol_code, price, position_pct, operation='buy', price_type=0):
        """调用第三方单笔交易API"""
        path = f"/qmt/trade/api/outer/trade/{operation}"
        data = {
            "trader_index": self.trader_index,
            "symbol": symbol_code,
            "trade_price": price,
            "price_type": price_type,
            "position_pct": position_pct,  # 仓位
            "strategy_name": self.strategy_name
        }
        return self._post(path, data)

    def _get(self, path, query_string=""):
        timestamp = str(int(time.time()))
        signature = generate_signature('GET', path, query_string, "", timestamp, self.client_id, self.secret_key)
        headers = {
            'Content-Type': 'application/json',
            'X-Client-ID': self.client_id,
            'X-Timestamp': timestamp,
            'X-Signature': signature
        }
        response = requests.get(f"{self.base_url}{path}?{query_string}", headers=headers)
        return response.json()

    def get_accounts(self):
        """获取账户列表"""
        path = "/qmt/trade/api/accounts"
        return self._get(path)

    def get_portfolio(self):
        """
        获取指定账户的资产信息
        Args:
            trader_index: 账户索引

        Returns:
            {
              'cash': 1.0,          # 可用资金
              'frozen_cash': 0.0,   # 冻结资金
              'market_value': 0.0,  # 总市值
              'profit': 0,          # 总盈亏
              'profit_ratio': 0,    # 总盈亏比例
              'total_asset': 1.0    # 总资产
            }
        """
        path = f"/qmt/trade/api/portfolio/{self.trader_index}"
        return self._get(path).get('portfolio')

    def get_positions(self):
        """获取指定账户的持仓信息"""
        path = f"/qmt/trade/api/positions/{self.trader_index}"
        return self._get(path).get('positions')

    @property
    def hold_positions(self):
        """获取指定账户的持仓信息, 只返回持仓数量大于0的"""
        positions = self.get_positions()
        return [pos for pos in positions if pos.get('volume', 0) > 0 and (not pos.get('symbol').startswith(('13', '20')))]

    @property
    def cash(self):
        return self.get_portfolio()['cash']

    def trade_allin(self, symbol_code, cur_price):
        """调用全仓买入接口"""
        path = "/qmt/trade/api/trade/allin"
        data = {"trader_index": self.trader_index, "symbol": symbol_code, "cur_price": cur_price}
        return self._post(path, data)

    def nhg(self):
        """调用逆回购接口"""
        path = "/qmt/trade/api/trade/nhg"
        data = {'trader_index': self.trader_index}
        return self._post(path, data)

    def cancel_all_orders_sale(self):
        """调用取消所有卖单接口"""
        path = "/qmt/trade/api/cancel_orders/sale"
        data = {'trader_index': self.trader_index}
        return self._post(path, data)

    def cancel_all_orders_buy(self):
        """调用取消所有买单接口"""
        path = "/qmt/trade/api/cancel_orders/buy"
        data = {'trader_index': self.trader_index}
        return self._post(path, data)

    def cancel_order(self, order_id):
        """取消订单"""
        path = "/qmt/trade/api/cancel_order"
        data = {'order_id': order_id, 'trader_index': self.trader_index}
        return self._post(path, data)

    def query_order(self, order_id):
        """查询订单状态"""
        path = f"/qmt/trade/api/order"
        data = {'order_id': order_id, 'trader_index': self.trader_index}
        return self._post(path, data)

    def query_orders(self, cancelable_only=False):
        """查询所有订单"""
        path = f"/qmt/trade/api/orders"
        data = {'trader_index': self.trader_index, 'cancelable_only': cancelable_only}
        return self._post(path, data)
