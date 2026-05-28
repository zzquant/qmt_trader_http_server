from flask import Blueprint, jsonify, request
import qmt_data
from logger_config import get_logger
from authentication import login_or_signature_required


def handle_exceptions(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            log.error(f"接口异常 [{f.__name__}]: {str(e)}", exc_info=True)
            return jsonify({'error': f'接口异常: {f.__name__}', 'message': str(e)}), 500
    return decorated_function


data_bp = Blueprint('data', __name__, url_prefix='/qmt/data/api')
log = get_logger(__name__)


@data_bp.route('/get_market_data_ex', methods=['GET'])
@login_or_signature_required
@handle_exceptions
def get_market_data_ex():
    """获取历史行情数据

    参数（query string）:
        stock_list: 股票代码，多个用逗号分隔，如 515050,000001
        field_list: 字段列表，多个用逗号分隔，如 open,high,low,close（可选）
        period: K线周期，默认 1d
        start_time: 起始时间，格式 YYYYMMDD（可选，默认60天前）
        end_time: 结束时间，格式 YYYYMMDD（可选，默认今天）
        count: 数据条数，默认 -1（全部）
        dividend_type: 复权方式，默认 front
        fill_data: 是否补全数据，默认 true
        json: 设为1返回JSON对象数组格式，默认0返回DataFrame友好格式
    """
    stock_list = request.args.get('stock_list', '')
    if not stock_list:
        return jsonify({'error': '缺少必要参数: stock_list'}), 400
    stock_list = [s.strip() for s in stock_list.split(',') if s.strip()]

    field_list = request.args.get('field_list', '')
    field_list = [f.strip() for f in field_list.split(',') if f.strip()] if field_list else []

    period = request.args.get('period', '1d')
    start_time = request.args.get('start_time', '')
    end_time = request.args.get('end_time', '')
    count = int(request.args.get('count', -1))
    dividend_type = request.args.get('dividend_type', 'front')
    fill_data = request.args.get('fill_data', 'true').lower() == 'true'
    as_json = request.args.get('json', '0') == '1'

    result = qmt_data.get_market_data_ex(
        stock_list=stock_list,
        field_list=field_list,
        period=period,
        start_time=start_time,
        end_time=end_time,
        count=count,
        dividend_type=dividend_type,
        fill_data=fill_data,
        as_json=as_json
    )

    return jsonify({'status': 'success', 'data': result})


@data_bp.route('/get_full_tick', methods=['GET'])
@login_or_signature_required
@handle_exceptions
def get_full_tick():
    """获取实时行情快照

    参数（query string）:
        stock_list: 股票代码，多个用逗号分隔，如 510300,515050
    """
    stock_list = request.args.get('stock_list', '')
    if not stock_list:
        return jsonify({'error': '缺少必要参数: stock_list'}), 400
    stock_list = [s.strip() for s in stock_list.split(',') if s.strip()]

    result = qmt_data.get_full_tick(stock_list=stock_list)

    return jsonify({'status': 'success', 'data': result})


