import math
import sys
import time
import traceback
import pandas as pd
import symbol_util
from xtquant import xtconstant
from xtquant.xttrader import XtQuantTrader, XtQuantTraderCallback
from xtquant.xttype import StockAccount
from dingtalk_helper import DingTalkBot
from logger_config import get_logger
from config import get_config

# 设置日志
log = get_logger(__name__)
config = get_config()
dingbot = DingTalkBot(config.dingtalk.access_token, config.dingtalk.secret)

ORDER_STATUS_MAP = {
    48: "未报",
    49: "待报",
    50: "已报",
    51: "已报待撤",
    52: "部成待撤",
    53: "部撤",
    54: "已撤",
    55: "部成",
    56: "已成",
    57: "废单",
    255: "未知",
}


class MyXtQuantTraderCallback(XtQuantTraderCallback):
    def on_disconnected(self):
        """
        连接断开
        :return:
        """
        log.info("connection lost, 交易接口断开，即将重连")
        # global xt_trader
        # xt_trader = None

    def on_stock_order(self, order):
        """
        委托回报推送
        :param order: XtOrder对象
        :return:
        """
        log.info(f"on order callback: {order.stock_code} {order.order_status}")
        # log.info(order.stock_code, order.order_status, order.order_sysid)

    def on_stock_asset(self, asset):
        """
        资金变动推送 注意，该回调函数目前不生效
        :param asset: XtAsset对象
        :return:
        """
        log.info(f"on asset callback {asset}")
        # log.info(asset.account_id, asset.cash, asset.total_asset)

    def on_stock_trade(self, trade):
        """
        成交变动推送
        :param trade: XtTrade对象
        :return:
        """
        log.info(f"on trade callback {trade}")
        # log.info(trade.account_id, trade.stock_code, trade.order_id)

    def on_stock_position(self, position):
        """
        持仓变动推送 注意，该回调函数目前不生效
        :param position: XtPosition对象
        :return:
        """
        log.info(f"on position callback {position}")
        # log.info(position.stock_code, position.volume)

    def on_order_error(self, order_error):
        """
        委托失败推送
        :param order_error:XtOrderError 对象
        :return:
        """
        # log.info(f"on order_error callback {order_error}")
        log.info(
            f"order_error {order_error.account_id}, {order_error.strategy_name}, {order_error.error_id}, {order_error.error_msg}")

    def on_cancel_error(self, cancel_error):
        """
        撤单失败推送
        :param cancel_error: XtCancelError 对象
        :return:
        """
        log.info(f"on cancel_error callback {cancel_error}")
        # log.info(cancel_error.order_id, cancel_error.error_id, cancel_error.error_msg)

    def on_order_stock_async_response(self, response):
        """
        异步下单回报推送
        :param response: XtOrderResponse 对象
        :return:
        """
        log.info(f"on_order_stock_async_response {response}")
        # log.info(response.account_id, response.order_id, response.seq)

    def on_account_status(self, status):
        """
        :param response: XtAccountStatus 对象
        :return:
        """
        # 账号状态映射
        status_map = {
            -1: "无效",
            0: "正常",
            1: "连接中",
            2: "登陆中",
            3: "失败",
            4: "初始化中",
            5: "数据刷新校正中",
            6: "收盘后",
            7: "穿透副链接断开",
            8: "系统停用（密码错误超限）",
            9: "用户停用"
        }

        status_text = status_map.get(status.status, f"未知状态({status.status})")
        log.info(f"on_account_status {status.account_id} {status.account_type} {status.status}({status_text})")
        # log.info(status.account_id, status.account_type, status.status)


class MyTradeAPIWrapper:
    def __init__(self, account_id, quant_code, nick_name="", qmtpath=None):
        self.account_id = account_id  # 账号id，对应你的交易账号id
        self.quant_code = quant_code  # 策略名称，用于区分多个策略
        self.nick_name = nick_name  # 账号名称，用于区分多个账号
        # 如果没有提供qmtpath，使用默认的D盘路径
        if qmtpath is None:
            qmtpath = r"D:\迅投极速策略交易系统交易终端 华鑫证券QMT实盘\userdata_mini"
        self.path = qmtpath
        self.session_id = quant_code * 1000000000 + int(account_id)  # xt接口需要的区分不同账号的session_id，同一个账号可以多次登录

        self.trade_api = None
        self.acc = None
        self.connect_trade_api()

    def connect_trade_api(self):
        """初始化或重新连接TradeAPI"""
        global xt_trader
        for attempt in range(3):
            try:
                self.session_id += 1
                log.info(f"init qmt安装路径:{self.path} account_id={self.account_id} {self.session_id}")
                xt_trader = XtQuantTrader(self.path, self.session_id)
                # 开启主动请求接口的专用线程 开启后在on_stock_xxx回调函数里调用XtQuantTrader.query_xxx函数不会卡住回调线程，但是查询和推送的数据在时序上会变得不确定
                # 详见: http://docs.thinktrader.net/vip/pages/ee0e9b/#开启主动请求接口的专用线程
                # http://dict.thinktrader.net/nativeApi/xttrader.html
                # xt_trader.set_relaxed_response_order_enabled(True)
                acc = StockAccount(self.account_id,
                                   'STOCK')  # StockAccount可以用第二个参数指定账号类型，如沪港通传'HUGANGTONG'，深港通传'SHENGANGTONG'
                callback = MyXtQuantTraderCallback()
                xt_trader.register_callback(callback)
                xt_trader.start()  # 启动交易线程
                connect_result = xt_trader.connect()
                log.info(f"{self.account_id} connect_result={connect_result}")
                if connect_result == 0:
                    log.info(f"{self.account_id} connected to TradeAPI success")
                    subscribe_result = xt_trader.subscribe(acc)
                    if subscribe_result != 0:
                        log.info('账号订阅失败 %d' % subscribe_result)
                        sys.exit('账号订阅失败，程序即将退出 %d' % connect_result)
                    else:
                        log.info('账号订阅成功 %d' % subscribe_result)
                    self.trade_api = xt_trader
                    self.acc = acc
                    return
                log.info(f"{self.account_id} connected to TradeAPI on attempt {attempt}")
            except Exception as e:
                log.info(f"{self.account_id} attempt {attempt} unexpected error: {e}")
            time.sleep(1)
        msg = f"Failed to connect TradeAPI for {self.account_id} after 3 attempts"
        log.info(msg)
        send_msg(msg)
        sys.exit('链接失败，程序即将退出 %d' % connect_result)

    def trade_target_pct(self, symbol, cur_price, pct_target=0.1, price_type=0, record=1):
        """指定仓位买入
        symbol: 股票代码
        cur_price: 当前价格
        pct_target: 仓位比例
        price_type: 0：限价
        """
        for _ in range(3):
            try:
                _portfolio = self.get_portfolio()
                total_value = _portfolio.total_asset
                available_cash = _portfolio.cash
                value = total_value * pct_target
                if value > available_cash:
                    value = available_cash
                result = self.trade_buy(symbol, cur_price, value, price_type, record)
                send_msg(result)
                return result
            except Exception as e:
                self.connect_trade_api()  # 重新连接TradeAPI
                log.error(traceback.format_exc())
                if _ == 2:  # 最后一次重试失败
                    return {
                        'success': False,
                        'symbol': symbol,
                        'order_num': 0,
                        'price': cur_price,
                        'value': 0,
                        'order_result': None,
                        'message': f'获取账户信息失败，重试3次后仍然失败: {str(e)}'
                    }
                continue

    def trade_sell_target_pct(self, symbol, cur_price, pct_target, price_type=0):
        """指定仓位卖出
        symbol: 股票代码
        cur_price: 当前价格
        pct_target: 仓位比例,持仓的仓位比例，如果全部卖出就是1，卖出半仓就是0.5
        """
        log.info("%s sell %s %s" % (self.account_id, symbol, cur_price))
        symbol = symbol_convert(symbol)
        _p = self.get_position()
        if symbol in _p:
            if hasattr(_p[symbol], 'can_use_volume'):
                order_num = _p[symbol].can_use_volume
            else:
                order_num = _p[symbol].get('can_use_volume', 0)
            order_num_sell = order_num * pct_target
            order_num_sell = int(order_num_sell / 100) * 100
            result = self.trade_sell(symbol, cur_price, order_num_sell, price_type)
            send_msg(result)
            return result
        else:
            return {
                'success': False,
                'symbol': symbol,
                'order_num': 0,
                'price': cur_price,
                'value': 0,
                'order_result': None,
                'message': f'未持有该股票: {symbol}'
            }

    def get_position(self, available_type=-2):
        """获取持仓
        available_type: 1：旧持仓，可用量>0 0：新买的，不可卖出 -1：无论新旧持仓都算 -2：无论是否持仓都算
                account_type	int	账号类型，参见数据字典
                account_id	str	资金账号
                stock_code	str	证券代码
                volume	int	持仓数量
                can_use_volume	int	可用数量
                open_price	float	开仓价
                market_value	float	市值
                frozen_volume	int	冻结数量
                on_road_volume	int	在途股份
                yesterday_volume	int	昨夜拥股
                avg_price	float	成本价
                direction	int	多空方向，股票不适用；参见数据字典
        """
        for _ in range(3):
            try:
                _p = {}
                positions = self.trade_api.query_stock_positions(self.acc)
                # 处理positions可能是字典或列表的情况
                if isinstance(positions, dict):
                    position_items = positions.items()
                elif isinstance(positions, list):
                    # 如果是列表，假设每个元素都有stock_code属性
                    position_items = [(getattr(pos, 'stock_code', str(i)), pos) for i, pos in enumerate(positions)]
                else:
                    log.error(f"Unexpected positions type: {type(positions)}")
                    continue

                for stock_code, position_info in position_items:
                    # 确保stock_code是字符串类型
                    if hasattr(position_info, 'stock_code'):
                        stock_code = position_info.stock_code
                    elif isinstance(stock_code, str):
                        pass  # stock_code已经是字符串
                    else:
                        stock_code = str(stock_code)

                    # if stock_code.startswith("SHR"):
                    #     continue
                    # if stock_code.startswith("13"):
                    #     continue
                    # if stock_code.startswith("S"):
                    #     continue
                    # if stock_code.startswith("5"):
                    #     continue

                    # 获取持仓信息，支持XtPosition对象和字典两种格式
                    if hasattr(position_info, 'can_use_volume'):
                        can_use_volume = position_info.can_use_volume
                        volume = position_info.volume
                        pos_data = position_info
                    else:
                        can_use_volume = position_info.get('can_use_volume', 0)
                        volume = position_info.get('volume', 0)
                        pos_data = position_info

                    if available_type == 1 and can_use_volume > 0:
                        _p[stock_code] = pos_data
                    elif available_type == 0 and can_use_volume == 0 and volume > 0:
                        _p[stock_code] = pos_data
                    elif available_type == -1 and volume > 0:
                        _p[stock_code] = pos_data
                    elif available_type == -2:
                        _p[stock_code] = pos_data
                return _p
            except Exception as e:
                log.info(f"Error getting positions: {e}")
                time.sleep(1)
                self.connect_trade_api()  # 重新连接TradeAPI

    def get_position_arr(self, available_type=1):
        stock_arr = []
        positions = self.get_position(available_type)
        return [item for item in positions if not str(item).startswith("SHR")]
        # for symbol in positions:
        #   stock_arr.append(symbol)
        # return stock_arr

    def get_position_arr_10(self, available_type=1):
        stock_arr = self.get_position_arr(available_type)
        return [item for item in stock_arr if not str(item).startswith(("30", "8", "4"))]

    def get_position_arr_20(self, available_type=1):
        stock_arr = self.get_position_arr(available_type)
        return [item for item in stock_arr if str(item).startswith("30")]

    def get_position_arr_kc(self, available_type=1):
        stock_arr = self.get_position_arr(available_type)
        return [item for item in stock_arr if str(item).startswith(("68"))]

    def get_position_arr_bj(self, available_type=1):
        stock_arr = self.get_position_arr(available_type)
        return [item for item in stock_arr if str(item).startswith(("8", "4"))]

    def get_position_df(self):
        positions = self.get_position()
        log.info(positions)
        vb_list = ['account_type', 'account_id', 'stock_code', 'volume', 'can_use_volume', 'open_price', 'market_value',
                   'frozen_volume', 'on_road_volume', 'yesterday_volume',
                   'avg_price', 'direction']
        positions_df = pd.DataFrame(columns=vb_list)
        # for symbol, info in positions.items():
        #   temp = pd.DataFrame([info], columns=vb_list)
        #   positions_df = pd.concat([positions_df, temp], ignore_index=True)
        # positions_df = pd.DataFrame()
        for symbol, info in positions.items():
            # 处理XtPosition对象和字典两种格式
            row_data = []
            for vb in vb_list:
                if hasattr(info, vb):
                    # XtPosition对象，直接访问属性
                    row_data.append(getattr(info, vb))
                elif isinstance(info, dict):
                    # 字典格式，使用键访问
                    row_data.append(info.get(vb, None))
                else:
                    # 其他情况，设为None
                    row_data.append(None)

            temp = pd.DataFrame([row_data], columns=vb_list, index=[0])
            positions_df = pd.concat([positions_df, temp], ignore_index=True)
        return positions_df

    def get_portfolio(self):
        for _ in range(2):
            try:
                return self.trade_api.query_stock_asset(self.acc)
            except Exception as e:
                log.info(f"Error get_portfolio: {e}")
                self.connect_trade_api()  # 重新连接TradeAPI

    def trade_buy(self, symbol, cur_price, value, price_type=0, record=1):
        try:
            strategy_name = f"quant_{self.quant_code}"
            _portfolio = self.get_portfolio()
            available_cash = _portfolio.cash
            if value > available_cash:
                value = available_cash
            symbol = symbol_convert(symbol)
            order_num = math.floor(value / cur_price / 100) * 100
            log.info(f"{strategy_name} buy {symbol} {order_num}")
            if order_num > 0:
                for _ in range(3):
                    try:
                        return self.order_dif_type(cur_price, order_num, price_type, strategy_name, symbol)
                    except Exception as e:
                        msg = f"{self.account_id} order retry {_} TradeAPI Error"
                        send_msg(msg)
                        log.error(msg + f"e: {e}")
                        self.connect_trade_api()  # 重新连接TradeAPI
                        if _ == 2:  # 最后一次重试失败
                            return {
                                'success': False,
                                'symbol': symbol,
                                'order_num': order_num,
                                'price': cur_price,
                                'error': str(e),
                                'message': f'买入订单提交失败: {symbol} {order_num}股 @{cur_price}, 错误: {str(e)}'
                            }
                        continue
                if record == 1:
                    # self._record_trade(symbol, order_num, cur_price)
                    pass
            else:
                if value > available_cash:
                    log.info(f"{self.account_id} money={value} not enough")
                    return {
                        'success': False,
                        'symbol': symbol,
                        'order_num': 0,
                        'price': cur_price,
                        'error': 'Insufficient funds',
                        'message': f'资金不足: 需要{value}, 可用{available_cash}'
                    }
                else:
                    log.info(f"{self.account_id} money={value} not enough to buy 100股")
                    return {
                        'success': False,
                        'symbol': symbol,
                        'order_num': 0,
                        'price': cur_price,
                        'error': 'Insufficient funds',
                        'message': f'指定仓位资金不足: 最低100股需要:{cur_price * 100:.2f}, 当前可用:{available_cash}'
                    }

        except Exception as e:
            log.error(traceback.format_exc())
            return {
                'success': False,
                'symbol': symbol if 'symbol' in locals() else '',
                'order_num': 0,
                'price': cur_price,
                'error': str(e),
                'message': f'买入操作异常: {str(e)}'
            }

    def order_dif_type(self, cur_price, order_num, price_type, strategy_name, symbol, order_type=xtconstant.STOCK_BUY):
        """
        根据不同的价格类型进行下单

        Args:
            cur_price (float): 当前价格 (限价单时使用)
            order_num (int): 委托数量
            price_type (int): 价格类型 (0:限价, 1:最新价, 2:最优五档即时成交剩余撤销, 3:本方最优, 5:对方最优)
            strategy_name (str): 策略名称
            symbol (str): 证券代码，格式如 '600000.SH' 或 '000001.SZ'
            order_type: int: 订单类型，xtconstant.STOCK_BUY 或 xtconstant.STOCK_SELL

        Returns:
            dict: 包含下单结果的字典
        """
        order_result = None
        price_type_map = {
            # 指定价格下单
            0: (xtconstant.FIX_PRICE, cur_price),
            # 最新价下单
            1: (xtconstant.LATEST_PRICE, 0),
            # 最优五档即时成交剩余撤销
            2: (
                xtconstant.MARKET_SH_CONVERT_5_CANCEL if symbol.endswith(
                    "SH") else xtconstant.MARKET_SZ_CONVERT_5_CANCEL,
                0),
            # 本方最优价格委托，买入时买一 卖出时卖一
            3: (xtconstant.MARKET_MINE_PRICE_FIRST, 0),
            # 对方最优价格委托，买入时卖一 卖出时买一
            5: (xtconstant.MARKET_PEER_PRICE_FIRST, 0)
        }

        if price_type not in price_type_map:
            return {
                'success': False,
                'message': f'错误：不支持的价格类型 {price_type}'
            }

        order_price_type, order_price = price_type_map[price_type]

        # 统一的下单逻辑
        try:
            order_result = self.trade_api.order_stock(
                self.acc, symbol, order_type, order_num,
                order_price_type, order_price, strategy_name
            )
        except Exception as e:
            return {
                'success': False,
                'message': f'下单时发生异常: {e}'
            }

        # 检查基本的下单响应
        if not order_result or order_result == -1:
            return {
                'success': False,
                'symbol': symbol,
                'order_num': order_num,
                'price': cur_price,
                'message': f'买入订单提交失败: {symbol} {order_num}股 @{cur_price}'
            }

        # 返回限价单的成功结果
        return {
            'success': True,
            'symbol': symbol,
            'order_num': order_num,
            'price': cur_price,
            'value': order_num * cur_price,  # 注意：这是委托价值，非成交价值
            'order_id': order_result,
            'message': f'买入限价单提交成功: {symbol} {order_num}股 @{cur_price}, OrderID: {order_result}'
        }

    def trade_buy_shares(self, symbol, cur_price, shares, price_type=0, record=1):
        """按固定股数买入股票"""
        try:
            strategy_name = f"quant_{self.quant_code}"
            _portfolio = self.get_portfolio()
            available_cash = _portfolio.cash

            # 计算所需资金
            required_value = shares * cur_price
            if required_value > available_cash:
                log.info(f"{self.account_id} 资金不足: 需要{required_value}, 可用{available_cash}")
                # 按可用资金调整股数
                shares = math.floor(available_cash / cur_price / 100) * 100
                if shares <= 0:
                    log.info(f"{self.account_id} 资金不足，无法买入")
                    return {
                        'success': False,
                        'symbol': symbol,
                        'order_num': 0,
                        'price': cur_price,
                        'value': 0,
                        'order_result': None,
                        'message': f'资金不足，无法买入: 需要{required_value}, 可用{available_cash}'
                    }

            symbol = symbol_convert(symbol)
            # 确保股数是100的倍数
            order_num = int(shares / 100) * 100
            value = order_num * cur_price

            if order_num > 0:
                for _ in range(3):
                    try:
                        order_result = self.order_dif_type(cur_price, order_num, price_type, strategy_name, symbol)

                        if record == 1:
                            # self._record_trade(symbol, order_num, cur_price)
                            pass

                        return {
                            'success': True,
                            'symbol': symbol,
                            'order_num': order_num,
                            'price': cur_price,
                            'value': value,
                            'order_result': order_result,
                            'message': f'买入订单提交成功: {symbol} {order_num}股 价格{cur_price}'
                        }
                    except Exception as e:
                        msg = f"{self.account_id} order retry {_} TradeAPI Error"
                        send_msg(msg)
                        log.error(msg + f"e: {e}")
                        self.connect_trade_api()
                        if _ == 2:  # 最后一次重试失败
                            return {
                                'success': False,
                                'symbol': symbol,
                                'order_num': order_num,
                                'price': cur_price,
                                'value': value,
                                'order_result': None,
                                'message': f'买入失败，重试3次后仍然失败: {str(e)}'
                            }
                        continue
            else:
                log.info(f"{self.account_id} 股数={shares} 不足100股")
                return {
                    'success': False,
                    'symbol': symbol,
                    'order_num': order_num,
                    'price': cur_price,
                    'value': 0,
                    'order_result': None,
                    'message': f'股数不足100股: {shares}'
                }
        except Exception as e:
            log.error(traceback.format_exc())
            return {
                'success': False,
                'symbol': symbol,
                'order_num': 0,
                'price': cur_price,
                'value': 0,
                'order_result': None,
                'message': f'买入异常: {str(e)}'
            }

    def trade_allin(self, symbol, cur_price):
        self.trade_target_pct(symbol, cur_price, 1)

    def nhg(self):
        """逆回购"""
        value = self.get_portfolio().cash
        order_num = math.floor(value / 100 / 10) * 10
        if order_num > 0:
            self.trade_api.order_stock(self.acc, "131810.SZ", xtconstant.STOCK_BUY, order_num, xtconstant.LATEST_PRICE,
                                       0)
            # self.trade_api.order("131990.SH", -order_num, 1)

    def trade_sell(self, symbol, cur_price, order_num, price_type=0):
        """执行卖出操作，并更新持仓"""
        try:  # 不让账户相互之间有冲突，比如登录失效不影响下面的
            log.info("%s sell %s %s %s" % (self.account_id, symbol, cur_price, order_num))
            symbol = symbol_convert(symbol)
            _p = self.get_position()
            if symbol in _p:
                if order_num is None or order_num == 0:
                    if hasattr(_p[symbol], 'can_use_volume'):
                        order_num = _p[symbol].can_use_volume
                    else:
                        order_num = _p[symbol].get('can_use_volume', 0)
                log.info("%s: do sell %s %s %s" % (self.account_id, symbol, cur_price, order_num))
                if order_num >= 100:
                    value = order_num * cur_price
                    order_result = self.order_dif_type(cur_price, order_num, price_type, f"quant_{self.quant_code}", symbol, xtconstant.STOCK_SELL)

                    return {
                        'success': True,
                        'symbol': symbol,
                        'order_num': order_num,
                        'price': cur_price,
                        'value': value,
                        'order_result': order_result,
                        'message': f'卖出订单提交成功: {symbol} {order_num}股 价格{cur_price}'
                    }
                else:
                    log.info("order_num error %s %s" % (symbol, order_num))
                    return {
                        'success': False,
                        'symbol': symbol,
                        'order_num': order_num,
                        'price': cur_price,
                        'value': 0,
                        'order_result': None,
                        'message': f'卖出股数不足100股: {order_num}'
                    }
            else:
                return {
                    'success': False,
                    'symbol': symbol,
                    'order_num': 0,
                    'price': cur_price,
                    'value': 0,
                    'order_result': None,
                    'message': f'未持有该股票: {symbol}'
                }
        except Exception as e:
            log.error(traceback.format_exc())
            return {
                'success': False,
                'symbol': symbol,
                'order_num': order_num,
                'price': cur_price,
                'value': 0,
                'order_result': None,
                'message': f'卖出异常: {str(e)}'
            }

    def cancel_all_orders_sale(self):
        self.cancel_all_orders(xtconstant.STOCK_SELL)

    def cancel_all_orders_buy(self):
        self.cancel_all_orders(xtconstant.STOCK_BUY)

    def cancel_all_orders(self, sideType):
        self.query_orders()
        for order in self.trade_api.query_stock_orders(self.acc, cancelable_only=True):
            order_id = order.order_id
            status = order.order_status
            order_type = order.order_type
            if order_type == sideType and status in [xtconstant.ORDER_REPORTED, xtconstant.ORDER_PART_SUCC]:
                log.info("cancel_order %s" % (order_id))
                result = self.trade_api.cancel_order_stock(self.acc, order_id)
                send_msg(f"撤单 {self.account_id} {order} {'成功' if result == 0 else '失败'}")

    def cancel_order(self, order_id):
        """
        撤单
        order_id: 委托单号
        """
        result = self.trade_api.cancel_order_stock(self.acc, order_id)
        if result == 0:
            return {
                'success': True,
                'order_id': order_id,
                'message': f'撤单成功: OrderID {order_id}'
            }
        else:
            return {
                'success': False,
                'order_id': order_id,
                'message': f'撤单失败: OrderID {order_id}'
            }

    def query_orders(self, cancelable_only=False):
        """
        查询委托单
        status: 委托状态，参见数据字典，默认查询所有状态的委托单
        """
        orders = self.trade_api.query_stock_orders(self.acc, cancelable_only)
        return [
            {
                'order_id': order.order_id,
                'symbol': order.stock_code,
                'side': 'buy' if order.order_type == xtconstant.STOCK_BUY else 'sell',
                'status': order.order_status,
                'm_status': ORDER_STATUS_MAP.get(order.order_status),
                'volume': order.order_volume,
                'time': order.order_time,
                'price': order.price,
                'price_type': order.price_type,
                'traded_volume': order.traded_volume,
                'traded_price': order.traded_price,
                'strategy_name': order.strategy_name
            }
            for order in orders
        ]

    def query_order(self, order_id):
        order = self.trade_api.query_stock_order(self.acc, order_id)
        return {
            'order_id': order.order_id,
            'symbol': order.stock_code,
            'side': 'buy' if order.order_type == xtconstant.STOCK_BUY else 'sell',
            'status': order.order_status,
            'm_status': ORDER_STATUS_MAP.get(order.order_status),
            'volume': order.order_volume,
            'time': order.order_time,
            'price': order.price,
            'price_type': order.price_type,
            'traded_volume': order.traded_volume,
            'traded_price': order.traded_price,
            'strategy_name': order.strategy_name
        }


def send_msg(msg):
    dingbot.send_text(msg, at_all=False)
    log.info(f"dingbot send msg: {msg}")


def symbol_convert(stock_code):
    return symbol_util.get_stock_id_xt(stock_code)
