from flask import Blueprint, jsonify, request, session, redirect, url_for
import qmt_data
from logger_config import get_logger
from config import get_config
from functools import wraps
import hmac
import hashlib
import time
import json


# 通用异常处理装饰器
def handle_exceptions(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            log.error(f"接口异常 [{f.__name__}]: {str(e)}", exc_info=True)
            return jsonify({'error': f'接口异常: {f.__name__}', 'message': str(e)}), 500

    return decorated_function


# 登录验证装饰器
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return jsonify({'error': '未登录，请先登录'}), 401
        return f(*args, **kwargs)

    return decorated_function


# HMAC签名验证装饰器
def api_signature_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 从请求头中获取签名相关信息
        client_id = request.headers.get('X-Client-ID')
        timestamp = request.headers.get('X-Timestamp')
        signature = request.headers.get('X-Signature')

        if not all([client_id, timestamp, signature]):
            log.warning("缺少必要的签名验证参数")
            return jsonify({'error': '缺少必要的签名验证参数'}), 401

        # 从配置文件获取API配置
        config = get_config()
        api_config = config.api

        # 验证时间戳（防止重放攻击）
        try:
            request_time = int(timestamp)
            current_time = int(time.time())
            if abs(current_time - request_time) > api_config.signature_timeout:
                log.warning(f"请求时间戳过期: {timestamp}")
                return jsonify({'error': '请求时间戳过期'}), 401
        except ValueError:
            log.warning(f"无效的时间戳格式: {timestamp}")
            return jsonify({'error': '无效的时间戳格式'}), 401

        if not api_config.is_valid_client(client_id):
            log.warning(f"无效的客户端ID: {client_id}")
            return jsonify({'error': '无效的客户端ID'}), 401

        # 构建签名字符串
        method = request.method
        path = request.path
        query_string = request.query_string.decode('utf-8')
        body = ''
        if request.is_json and request.get_json():
            body = json.dumps(request.get_json(), sort_keys=True, separators=(',', ':'))

        # 签名字符串格式: METHOD\nPATH\nQUERY_STRING\nBODY\nTIMESTAMP\nCLIENT_ID
        sign_string = f"{method}\n{path}\n{query_string}\n{body}\n{timestamp}\n{client_id}"

        # 计算HMAC-SHA256签名
        secret_key = api_config.get_client_secret(client_id)
        expected_signature = hmac.new(
            secret_key.encode('utf-8'),
            sign_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        # 验证签名
        if not hmac.compare_digest(signature, expected_signature):
            log.warning(
                f"签名验证失败 - path:{path} Client: {client_id}, Expected: {expected_signature}, Got: {signature}")
            log.debug(f"签名字符串: {repr(sign_string)}")
            return jsonify({'error': '签名验证失败'}), 401

        log.info(f"签名验证成功 - Client: {client_id}")
        return f(*args, **kwargs)

    return decorated_function


def login_or_signature_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # ----------- 登录验证 -----------
        if 'logged_in' in session:
            return f(*args, **kwargs)

        # ----------- 签名验证 -----------
        client_id = request.headers.get('X-Client-ID')
        timestamp = request.headers.get('X-Timestamp')
        signature = request.headers.get('X-Signature')

        if not all([client_id, timestamp, signature]):
            return jsonify({'error': '未登录或缺少必要的签名验证参数'}), 401

        config = get_config()
        api_config = config.api

        # 验证时间戳
        try:
            request_time = int(timestamp)
            current_time = int(time.time())
            if abs(current_time - request_time) > api_config.signature_timeout:
                return jsonify({'error': '请求时间戳过期'}), 401
        except ValueError:
            return jsonify({'error': '无效的时间戳格式'}), 401

        if not api_config.is_valid_client(client_id):
            return jsonify({'error': '无效的客户端ID'}), 401

        # 构建签名字符串
        method = request.method
        path = request.path
        query_string = request.query_string.decode('utf-8')
        body = ''
        if method != "GET":
            if request.is_json and request.get_json():
                body = json.dumps(request.get_json(), sort_keys=True, separators=(',', ':'))

        sign_string = f"{method}\n{path}\n{query_string}\n{body}\n{timestamp}\n{client_id}"

        secret_key = api_config.get_client_secret(client_id)
        expected_signature = hmac.new(
            secret_key.encode('utf-8'),
            sign_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(signature, expected_signature):
            return jsonify({'error': '签名验证失败'}), 401

        # 签名验证成功
        return f(*args, **kwargs)

    return decorated_function


# 创建交易相关的蓝图
trade_bp = Blueprint('trade', __name__, url_prefix='/qmt/trade/api')

# 获取日志记录器
log = get_logger(__name__)

# 交易器实例将通过init_trade_routes函数注入
traders = []


def init_trade_routes(traders_list):
    """初始化交易路由，注入交易器实例"""
    global traders
    traders = traders_list
    log.info(f"交易路由初始化完成，共{len(traders)}个交易器")


@trade_bp.route('/accounts')
@login_or_signature_required
@handle_exceptions
def get_accounts():
    """获取账户列表"""
    log.info("获取账户列表")
    accounts = []

    for i, trader in enumerate(traders):
        accounts.append({
            'index': i,
            'account_id': trader.account_id,
            'nick_name': trader.nick_name or f"账户{i + 1}"
        })

    return jsonify({'accounts': accounts})


@trade_bp.route('/portfolio/<int:trader_index>')
@login_or_signature_required
@handle_exceptions
def get_portfolio(trader_index):
    """获取指定账户的资产信息"""
    log.info(f"获取交易器{trader_index}的资产信息")

    if trader_index >= len(traders):
        return jsonify({'error': '无效的交易器索引'}), 400

    trader = traders[trader_index]
    portfolio = trader.get_portfolio()

    if portfolio:
        # 处理XtAsset对象或字典格式
        if hasattr(portfolio, 'total_asset'):
            portfolio_data = {
                'total_asset': portfolio.total_asset,  # 总资产
                'cash': portfolio.cash,  # 可用金额
                'frozen_cash': portfolio.frozen_cash,  # 冻结金额
                'market_value': portfolio.market_value,  # 总市值
                'profit': getattr(portfolio, 'profit', 0),  # 盈亏
                'profit_ratio': getattr(portfolio, 'profit_ratio', 0)  # 盈亏比例
            }
        else:
            portfolio_data = {
                'total_asset': portfolio.get('total_asset', 0),
                'cash': portfolio.get('cash', 0),
                'frozen_cash': portfolio.get('frozen_cash', 0),
                'market_value': portfolio.get('market_value', 0),
                'profit': portfolio.get('profit', 0),
                'profit_ratio': portfolio.get('profit_ratio', 0)
            }

        return jsonify({'portfolio': portfolio_data})
    else:
        return jsonify({'error': '无法获取资产信息'}), 500


@trade_bp.route('/positions/<int:trader_index>')
@login_or_signature_required
@handle_exceptions
def get_positions(trader_index):
    """获取指定账户的持仓信息"""
    log.info(f"获取交易器{trader_index}的持仓信息")

    if trader_index >= len(traders):
        return jsonify({'error': '无效的交易器索引'}), 400

    trader = traders[trader_index]
    positions = trader.get_position()
    position_list = []

    for symbol, pos in positions.items():
        # 处理XtPosition对象或字典格式
        if hasattr(pos, 'volume'):
            # XtPosition对象格式
            volume = getattr(pos, 'volume', 0)
            can_use_volume = getattr(pos, 'can_use_volume', 0)
            frozen_volume = getattr(pos, 'frozen_volume', 0)
            market_value = getattr(pos, 'market_value', 0)
            avg_price = getattr(pos, 'avg_price', 0)
            open_price = getattr(pos, 'open_price', 0)
            log.info(
                f"持仓信息 - 股票代码: {symbol}, 持仓数量: {volume}, 可用数量: {can_use_volume}, 冻结数量: {frozen_volume}, 市值: {market_value}, 成本价: {avg_price}, 开仓价: {open_price}")

            # 打印pos对象的所有属性（调试用）
            # log.debug(f"pos对象类型: {type(pos)}")
            # log.debug(f"pos对象所有属性: {[attr for attr in dir(pos) if not attr.startswith('_')]}")
            # pos对象所有属性: ['account_id', 'account_type', 'avg_price', 'can_use_volume', 'direction', 'float_profit', 'frozen_volume', 'instrument_name', 'last_price', 'm_dAvgPrice', 'm_dFloatProfit', 'm_dMarketValue', 'm_dOpenPrice', 'm_nAccountType', 'm_nCanUseVolume', 'm_nDirection', 'm_nFrozenVolume', 'm_nOnRoadVolume', 'm_nVolume', 'm_nYesterdayVolume', 'm_strAccountID', 'm_strStockCode', 'market_value', 'on_road_volume', 'open_date', 'open_price', 'position_profit', 'profit_rate', 'secu_account', 'stock_code', 'volume', 'yesterday_volume']
            # for attr in dir(pos):
            #     if not attr.startswith('_'):
            #         try:
            #             value = getattr(pos, attr)
            #             if not callable(value):
            #                 log.debug(f"pos.{attr} = {value} (类型: {type(value)})")
            #         except Exception as e:
            #             log.debug(f"获取pos.{attr}失败: {e}")
            # 如果market_value为0，尝试用volume * avg_price计算
            if market_value == 0 and volume > 0 and avg_price > 0:
                market_value = volume * avg_price

            # 计算盈亏和盈亏比例
            try:
                current_price = qmt_data.get_last_price(symbol)  # 获取实时价格
            except:
                current_price = avg_price
            try:
                symbol_name = qmt_data.get_instrument_detail(symbol)['InstrumentName']
            except:
                symbol_name = symbol

            cost_value = volume * avg_price if avg_price > 0 else 0
            current_value = volume * current_price if current_price > 0 else market_value
            profit = current_value - cost_value if cost_value > 0 else 0
            profit_ratio = (profit / cost_value * 100) if cost_value > 0 else 0

            position_data = {
                'symbol': symbol,
                'name': symbol_name,  # 暂时使用股票代码作为名称
                'volume': volume,  # 当前持股
                'can_use_volume': can_use_volume,  # 可用股数
                'frozen_volume': frozen_volume,  # 冻结数量
                'market_value': market_value,  # 市值
                'avg_price': avg_price,  # 成本价
                'open_price': open_price,  # 开仓价
                'current_price': current_price,  # 最新价
                'profit': profit,  # 盈亏
                'profit_ratio': profit_ratio  # 盈亏比例
            }
        else:
            # 字典格式
            volume = pos.get('volume', 0)
            can_use_volume = pos.get('can_use_volume', 0)
            frozen_volume = pos.get('frozen_volume', 0)
            market_value = pos.get('market_value', 0)
            avg_price = pos.get('avg_price', 0)
            open_price = pos.get('open_price', 0)

            # 如果market_value为0，尝试用volume * avg_price计算
            if market_value == 0 and volume > 0 and avg_price > 0:
                market_value = volume * avg_price

            # 计算盈亏和盈亏比例
            current_price = avg_price  # 暂时使用成本价作为当前价
            cost_value = volume * avg_price if avg_price > 0 else 0
            current_value = volume * current_price if current_price > 0 else market_value
            profit = current_value - cost_value if cost_value > 0 else 0
            profit_ratio = (profit / cost_value * 100) if cost_value > 0 else 0

            position_data = {
                'symbol': symbol,
                'name': symbol,
                'volume': volume,
                'can_use_volume': can_use_volume,
                'frozen_volume': frozen_volume,
                'market_value': market_value,
                'avg_price': avg_price,
                'open_price': open_price,
                'current_price': current_price,  # 最新价
                'profit': profit,  # 盈亏
                'profit_ratio': profit_ratio  # 盈亏比例
            }

        position_list.append(position_data)

    log.info(f"交易器{trader_index}持仓信息获取成功，共{len(position_list)}只股票")
    return jsonify({'positions': position_list})


@trade_bp.route('/sell', methods=['POST'])
@login_required
@handle_exceptions
def sell_stock():
    """卖出股票"""
    data = request.get_json()
    if not data:
        return jsonify({'error': '请求数据不能为空'}), 400

    symbol = data.get('symbol')
    price = data.get('price')
    shares = data.get('shares')

    if not symbol or price is None or shares is None:
        return jsonify({'error': '缺少必要参数: symbol, price, shares'}), 400

    log.info(f"开始卖出: symbol={symbol}, price={price}, shares={shares}")

    results = []
    for i, trader in enumerate(traders):
        try:
            log.info(f"交易器{i}开始卖出")
            result = trader.trade_sell(symbol, price, shares)  # 使用正确的方法名
            results.append({'trader_index': i, 'result': result, 'status': 'success'})
            log.info(f"交易器{i}卖出完成: {result}")
        except Exception as e:
            error_msg = f"交易器{i}卖出失败: {str(e)}"
            log.error(error_msg, exc_info=True)
            results.append({'trader_index': i, 'error': error_msg, 'status': 'failed'})

    return jsonify({'message': '卖出执行完成', 'results': results})


@trade_bp.route('/trade', methods=['POST'])
@login_required
@handle_exceptions
def trade():
    """执行交易"""

    # 获取请求参数
    data = request.get_json()
    if not data:
        log.error("请求数据为空")
        return jsonify({"error": "请求数据不能为空"}), 400

    symbol = data.get('symbol')
    trade_price = data.get('trade_price')
    position_pct = data.get('position_pct')
    pricetype = data.get('pricetype', 0)

    # 参数验证
    if not symbol or trade_price is None or position_pct is None:
        log.error(f"参数不完整: symbol={symbol}, trade_price={trade_price}, position_pct={position_pct}")
        return jsonify({"error": "缺少必要参数: symbol, trade_price, position_pct"}), 400

    log.info(f"开始执行交易: symbol={symbol}, trade_price={trade_price}, position_pct={position_pct}")

    # 执行交易
    results = []
    for i, trader in enumerate(traders):
        try:
            log.info(f"交易器{i}开始执行交易")
            result = trader.trade_target_pct(symbol, trade_price, position_pct, pricetype)
            results.append({"trader_index": i, "result": result, "status": "success"})
            log.info(f"交易器{i}交易完成: {result}")
        except Exception as e:
            error_msg = f"交易器{i}交易失败: {str(e)}"
            log.error(error_msg, exc_info=True)
            results.append({"trader_index": i, "error": error_msg, "status": "failed"})

    log.info(f"所有交易器执行完成，结果: {results}")
    return jsonify({"message": "交易执行完成", "results": results})


@trade_bp.route('/outer/trade/<operation>', methods=['POST'])
@api_signature_required
@handle_exceptions
def outer_trade(operation):
    """第三方调用的交易接口（使用HMAC签名验证）"""
    if operation not in ['buy', 'sell']:
        return jsonify({"error": "操作类型必须是 buy 或 sell"}), 400

    # 获取请求参数
    data = request.get_json()
    if not data:
        log.error("第三方交易请求数据为空")
        return jsonify({"error": "请求数据不能为空"}), 400

    trader_index = data.get('trader_index')
    symbol = data.get('symbol')
    trade_price = data.get('trade_price')
    price_type = data.get('price_type', 0)
    position_pct = data.get('position_pct')
    strategy_name = data.get('strategy_name', '外部策略')

    # 参数验证
    if not symbol or trade_price is None or position_pct is None:
        log.error(
            f"第三方批量{operation}交易参数不完整: symbol={symbol}, trade_price={trade_price}, position_pct={position_pct}")
        return jsonify({"error": "缺少必要参数: symbol, trade_price, position_pct"}), 400

    if trader_index is not None and (trader_index >= len(traders) or trader_index < 0):
        log.error(f"无效的交易器索引: {trader_index}")
        return jsonify({"error": f"无效的交易器索引: {trader_index}"}), 400

    log.info(
        f"第三方开始执行{operation}交易: symbol={symbol}, trade_price={trade_price}, position_pct={position_pct}, strategy_name={strategy_name}")

    accounts = [traders[trader_index]] if trader_index is not None else traders
    # 执行交易
    results = []
    for i, trader in enumerate(accounts):
        try:
            log.info(f"第三方调用-交易器{i}开始执行{operation}交易")
            if operation == 'buy':
                result = trader.trade_target_pct(symbol, trade_price, position_pct, price_type)
            else:  # sell
                result = trader.trade_sell_target_pct(symbol, trade_price, position_pct, price_type)
            results.append({"trader_index": i, "result": result, "status": "success"})
            log.info(f"第三方调用-交易器{i}{operation}交易完成: {result}")
        except Exception as e:
            error_msg = f"第三方调用-交易器{i}{operation}交易失败: {str(e)}"
            log.error(error_msg, exc_info=True)
            results.append({"trader_index": i, "error": error_msg, "status": "failed"})

    log.info(f"第三方调用-所有交易器{operation}执行完成，结果: {results}")
    return jsonify({
        "message": f"第三方{operation}交易执行完成",
        "operation": operation,
        "strategy_name": strategy_name,
        "results": results
    })


@trade_bp.route('/trade/allin', methods=['POST'])
@api_signature_required
@handle_exceptions
def trade_allin():
    """全仓买入接口"""
    data = request.get_json()
    symbol = data.get('symbol')
    cur_price = data.get('cur_price')
    trader_index = data.get('trader_index')

    if not symbol or cur_price is None:
        return jsonify({'error': '缺少必要参数: symbol, cur_price'}), 400

    if trader_index is not None and (trader_index >= len(traders) or trader_index < 0):
        log.error(f"无效的交易器索引: {trader_index}")
        return jsonify({"error": f"无效的交易器索引: {trader_index}"}), 400

    results = []
    accounts = [traders[trader_index]] if trader_index is not None else traders
    for i, trader in enumerate(accounts):
        try:
            result = trader.trade_allin(symbol, cur_price)
            results.append({'trader_index': i, 'result': result, 'status': 'success'})
        except Exception as e:
            results.append({'trader_index': i, 'error': str(e), 'status': 'failed'})

    return jsonify({'message': '全仓买入完成', 'results': results})


@trade_bp.route('/trade/nhg', methods=['POST'])
@api_signature_required
@handle_exceptions
def nhg():
    """逆回购接口"""

    results = []
    data = request.get_json()
    trader_index = data.get('trader_index')
    if trader_index is not None and (trader_index >= len(traders) or trader_index < 0):
        log.error(f"无效的交易器索引: {trader_index}")
        return jsonify({"error": f"无效的交易器索引: {trader_index}"}), 400

    accounts = [traders[trader_index]] if trader_index is not None else traders
    for i, trader in enumerate(accounts):
        try:
            trader.nhg()
            results.append({'trader_index': i, 'status': 'success'})
        except Exception as e:
            results.append({'trader_index': i, 'error': str(e), 'status': 'failed'})

    return jsonify({'message': '逆回购完成', 'results': results})


@trade_bp.route('/cancel_orders/sale', methods=['POST'])
@api_signature_required
@handle_exceptions
def cancel_all_orders_sale():
    """取消所有卖单接口"""
    results = []
    data = request.get_json()
    trader_index = data.get('trader_index')
    if trader_index is not None and (trader_index >= len(traders) or trader_index < 0):
        log.error(f"无效的交易器索引: {trader_index}")
        return jsonify({"error": f"无效的交易器索引: {trader_index}"}), 400

    accounts = [traders[trader_index]] if trader_index is not None else traders
    for i, trader in enumerate(accounts):
        try:
            trader.cancel_all_orders_sale()
            results.append({'trader_index': i, 'status': 'success'})
        except Exception as e:
            results.append({'trader_index': i, 'error': str(e), 'status': 'failed'})

    return jsonify({'message': '取消所有卖单完成', 'results': results})


@trade_bp.route('/cancel_orders/buy', methods=['POST'])
@api_signature_required
@handle_exceptions
def cancel_all_orders_buy():
    """取消所有买单接口"""
    results = []
    data = request.get_json()
    trader_index = data.get('trader_index')
    if trader_index is not None and (trader_index >= len(traders) or trader_index < 0):
        log.error(f"无效的交易器索引: {trader_index}")
        return jsonify({"error": f"无效的交易器索引: {trader_index}"}), 400

    accounts = [traders[trader_index]] if trader_index is not None else traders
    for i, trader in enumerate(accounts):
        try:
            trader.cancel_all_orders_buy()
            results.append({'trader_index': i, 'status': 'success'})
        except Exception as e:
            results.append({'trader_index': i, 'error': str(e), 'status': 'failed'})

    return jsonify({'message': '取消所有买单完成', 'results': results})


@trade_bp.route('/cancel_order', methods=['POST'])
@api_signature_required
@handle_exceptions
def cancel_order():
    """撤单接口"""
    data = request.get_json()
    order_id = data.get('order_id')
    trader_index = data.get('trader_index')
    if trader_index is None or trader_index >= len(traders) or trader_index < 0:
        log.error(f"无效的交易器索引: {trader_index}")
        return jsonify({"error": f"无效的交易器索引: {trader_index}"}), 400

    trader = traders[trader_index]
    return jsonify(trader.cancel_order(order_id))


@trade_bp.route('/order', methods=['POST'])
@api_signature_required
@handle_exceptions
def order():
    """订单查询"""
    data = request.get_json()
    order_id = data.get('order_id')
    trader_index = data.get('trader_index')
    if trader_index is None or trader_index >= len(traders) or trader_index < 0:
        log.error(f"无效的交易器索引: {trader_index}")
        return jsonify({"error": f"无效的交易器索引: {trader_index}"}), 400

    trader = traders[trader_index]
    return jsonify(trader.query_order(order_id))


@trade_bp.route('/orders', methods=['POST'])
@api_signature_required
@handle_exceptions
def orders():
    """所有订单查询"""

    data = request.get_json()
    trader_index = data.get('trader_index')
    cancelable_only = data.get('cancelable_only', False)
    if trader_index is None or trader_index >= len(traders) or trader_index < 0:
        log.error(f"无效的交易器索引: {trader_index}")
        return jsonify({"error": f"无效的交易器索引: {trader_index}"}), 400

    trader = traders[trader_index]
    return jsonify(trader.query_orders(cancelable_only))
