from xtquant import xtdata
import time
from datetime import datetime, timedelta
from logger_config import get_logger
import symbol_util

log = get_logger(__name__)

def get_last_price(stock):
    full_tick = xtdata.get_full_tick([stock])
    current_price = full_tick[stock]['lastPrice']
    return current_price


def get_instrument_detail(stock_code, iscomplete=False):
    return xtdata.get_instrument_detail(stock_code, iscomplete)


def get_full_tick(stock_list, as_json=False):
    """获取实时行情快照

    Args:
        stock_list: 股票代码列表，如 ['510300', '515050']
        as_json: True返回原始dict格式，False返回带timeFmt的格式

    Returns:
        dict: {stock_code: 实时数据dict}
    """
    if not stock_list:
        raise ValueError('stock_list 不能为空')

    stock_list = [symbol_util.get_stock_id_xt(s) for s in stock_list]

    log.info(f"get_full_tick: stocks={stock_list}")

    result = xtdata.get_full_tick(stock_list)

    output = {}
    for stock, data in result.items():
        if data is None:
            output[stock] = {}
            continue
        data['timeFmt'] = data.get('timetag', '')
        output[stock] = data

    log.info(f"get_full_tick: 返回 {len(output)} 只股票数据")
    return output


def get_market_data_ex(stock_list, field_list=None, period='1d', start_time='', end_time='', count=-1, dividend_type='front', fill_data=True, as_json=False):
    """获取历史行情数据

    Args:
        stock_list: 股票代码列表，如 ['000001.SZ', '600000.SH']
        field_list: 字段列表，空或None表示全部字段
        period: K线周期，支持 '1m','5m','15m','30m','1h','1d','1w','1mon','tick'
        start_time: 起始时间，格式 'YYYYMMDD'，默认60天前
        end_time: 结束时间，格式 'YYYYMMDD'，默认今天
        count: 数据条数，-1表示全部
        dividend_type: 复权方式，'none','front','back','front_ratio','back_ratio'
        fill_data: 是否补全数据
        as_json: True返回对象数组格式，False返回DataFrame友好格式

    Returns:
        dict: {stock_code: DataFrame友好格式 或 对象数组格式}
    """
    if not stock_list:
        raise ValueError('stock_list 不能为空')

    stock_list = [symbol_util.get_stock_id_xt(s) for s in stock_list]

    if field_list is None:
        field_list = []

    if not start_time:
        start_time = (datetime.now() - timedelta(days=60)).strftime('%Y%m%d')
    if not end_time:
        end_time = datetime.now().strftime('%Y%m%d')

    log.info(f"get_market_data_ex: stocks={stock_list}, period={period}, start={start_time}, end={end_time}, dividend={dividend_type}")

    result = xtdata.get_market_data_ex(
        field_list=field_list,
        stock_list=stock_list,
        period=period,
        start_time=start_time,
        end_time=end_time,
        count=count,
        dividend_type=dividend_type,
        fill_data=fill_data
    )

    # 自动下载缺失数据
    empty_stocks = [stock for stock, df in result.items() if df is None or df.empty]
    if empty_stocks:
        log.info(f"自动下载缺失数据: {empty_stocks}")
        for stock in empty_stocks:
            xtdata.download_history_data(stock, period, start_time, end_time)
        time.sleep(1)
        result = xtdata.get_market_data_ex(
            field_list=field_list,
            stock_list=stock_list,
            period=period,
            start_time=start_time,
            end_time=end_time,
            count=count,
            dividend_type=dividend_type,
            fill_data=fill_data
        )

    # 日K数据用实时行情更新最后一天
    if period == '1d':
        today_str = datetime.now().strftime('%Y%m%d')
        tick_data = xtdata.get_full_tick(stock_list)
        for stock, df in result.items():
            if df is None or df.empty:
                continue
            tick = tick_data.get(stock)
            if not tick:
                continue
            last_idx = str(df.index[-1])
            if last_idx == today_str:
                row_idx = len(df) - 1
                if 'close' in df.columns:
                    df.at[df.index[row_idx], 'close'] = tick.get('lastPrice', df.iloc[row_idx]['close'])
                if 'high' in df.columns:
                    df.at[df.index[row_idx], 'high'] = max(df.iloc[row_idx]['high'], tick.get('high', 0))
                if 'low' in df.columns:
                    df.at[df.index[row_idx], 'low'] = min(df.iloc[row_idx]['low'], tick.get('low', float('inf')))
                if 'volume' in df.columns:
                    df.at[df.index[row_idx], 'volume'] = tick.get('volume', df.iloc[row_idx]['volume'])
                if 'amount' in df.columns:
                    df.at[df.index[row_idx], 'amount'] = tick.get('amount', df.iloc[row_idx]['amount'])

    # 转为输出格式
    output = {}
    for stock, df in result.items():
        if df is None or df.empty:
            output[stock] = [] if as_json else {'columns': [], 'index': [], 'data': []}
            continue
        columns = list(df.columns)
        data = df.values.tolist()
        if 'time' in columns:
            time_idx = columns.index('time')
            for row in data:
                ts_ms = row[time_idx]
                if ts_ms and ts_ms > 0:
                    row.append(datetime.fromtimestamp(ts_ms / 1000).strftime('%Y%m%d'))
                else:
                    row.append('')
            columns.append('timeFmt')

        if as_json:
            output[stock] = [dict(zip(columns, row)) for row in data]
        else:
            output[stock] = {
                'columns': columns,
                'index': [str(i) for i in df.index],
                'data': data
            }

    log.info(f"get_market_data_ex: 返回 {len(output)} 只股票数据")
    return output