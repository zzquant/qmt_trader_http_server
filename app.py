from flask import Flask, redirect, render_template, request, session, flash, url_for
from functools import wraps
from qmt_trade import MyTradeAPIWrapper
from trade_routes import trade_bp, init_trade_routes
from logger_config import setup_logging, get_logger
from config import get_config

# 获取配置
config = get_config()

# 初始化日志
log = setup_logging()

app = Flask(__name__)
# 使用统一配置
app.config.update(config.get_flask_config())

# 登录验证装饰器
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# 初始化交易器数组（使用配置文件）
traders = []
for trader_config in config.get_enabled_traders():
    trader = MyTradeAPIWrapper(
        trader_config.account_id,
        trader_config.account_type,
        trader_config.account_name,
        qmtpath=trader_config.qmt_path
    )
    traders.append(trader)
    log.info(f"初始化交易账户: {trader_config.account_name} ({trader_config.account_id})")

# 注册交易路由蓝图
app.register_blueprint(trade_bp)

# 初始化交易路由
init_trade_routes(traders)

@app.route('/')
def index():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    log.info("收到根路径请求，重定向到交易页面")
    return redirect('/trading')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username in config.auth.users and config.auth.users[username] == password:
            session.permanent = True  # 启用永久session
            session['logged_in'] = True
            session['username'] = username
            log.info(f"用户 {username} 登录成功，session设置为永久有效")
            return redirect(url_for('trading_page'))
        else:
            log.warning(f"用户 {username} 登录失败")
            return render_template('login.html', error='用户名或密码错误')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    username = session.get('username', '未知用户')
    session.clear()
    log.info(f"用户 {username} 已登出")
    return redirect(url_for('login'))

@app.route('/trading')
@login_required
def trading_page():
    """交易界面"""
    log.info(f"用户 {session.get('username')} 访问交易页面")
    return render_template('trading.html')


# 添加日志中间件
@app.before_request
def log_request_info():
    from flask import request
    # 过滤掉开发工具相关的请求
    if not any(path in request.path for path in ['@vite', 'favicon.ico', '__webpack']):
        log.info(f"请求: {request.method} {request.url} - IP: {request.remote_addr}")

@app.after_request
def log_response_info(response):
    from flask import request
    # 过滤掉开发工具相关的请求
    if not any(path in request.path for path in ['@vite', 'favicon.ico', '__webpack']):
        log.info(f"响应状态码: {response.status_code}")
    return response

# 404错误处理
@app.errorhandler(404)
def handle_404(e):
    from flask import request
    # 只记录非开发工具相关的404错误
    if not any(path in request.path for path in ['@vite', 'favicon.ico', '__webpack']):
        log.warning(f"404错误: {request.method} {request.path} - IP: {request.remote_addr}")
    return "Not Found", 404

# 其他异常处理
@app.errorhandler(Exception)
def handle_exception(e):
    from flask import request
    from werkzeug.exceptions import HTTPException
    
    # 如果是HTTP异常且是开发工具相关请求，不记录日志
    if isinstance(e, HTTPException) and any(path in request.path for path in ['@vite', 'favicon.ico', '__webpack']):
        return str(e), e.code
    
    # 记录真正的应用异常
    log.error(f"应用异常: {str(e)}", exc_info=True)
    return "Internal Server Error", 500

if __name__ == '__main__':
    log.info("启动Flask应用")
    log.info(f"服务器配置: {config.flask.host}:{config.flask.port}, Debug: {config.flask.debug}")
    app.run(debug=config.flask.debug, host=config.flask.host, port=config.flask.port)
    log.info("Flask应用已停止")
