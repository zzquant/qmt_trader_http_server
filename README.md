# QMT交易系统

一个基于Flask的QMT量化交易Web系统，提供完整的交易管理、持仓监控和用户认证功能。

## 项目简介

本项目是一个专为QMT（迅投极速策略交易系统）设计的Web交易界面，通过HTTP API的方式提供量化交易功能。系统集成了用户登录验证、实时持仓查询、交易执行、盈亏计算等核心功能。

## 主要功能

### 🔐 用户认证系统
- 安全的登录验证机制
- Session会话管理
- 用户权限控制
- 自动登录状态检查

### 📊 交易管理
- **实时持仓查询**：支持多账户持仓信息获取
- **资产组合监控**：实时显示总资产、可用资金、持仓市值
- **盈亏计算**：自动计算持仓盈亏和盈亏比例
- **交易执行**：支持买入、卖出操作
- **订单管理**：订单状态跟踪和管理

### 💻 Web界面
- **响应式设计**：支持桌面和移动端访问
- **实时数据更新**：自动刷新持仓和资产信息
- **美观的UI界面**：基于Bootstrap 5的现代化界面
- **用户友好**：直观的操作界面和状态提示

### 🔧 技术特性
- **RESTful API**：标准化的HTTP接口设计
- **多账户支持**：可同时管理多个交易账户
- **日志记录**：完整的操作日志和错误追踪
- **异常处理**：健壮的错误处理机制

## 技术架构

### 后端技术栈
- **Flask 2.3.3**：轻量级Web框架
- **Python 3.8+**：主要开发语言
- **xtquant**：QMT官方量化交易接口
- **pandas**：数据处理和分析
- **logging**：日志记录系统

### 前端技术栈
- **Bootstrap 5**：响应式UI框架
- **Bootstrap Icons**：图标库
- **JavaScript**：前端交互逻辑
- **Jinja2**：模板引擎

### 项目结构
```
qmt_trader_http_server/
├── app.py                 # Flask主应用
├── qmt_trade.py          # QMT交易接口封装
├── trade_routes.py       # 交易相关路由
├── qmt_data.py           # 数据获取模块
├── symbol_util.py        # 股票代码工具
├── requirements.txt      # 依赖包列表
├── templates/            # HTML模板
│   ├── login.html       # 登录页面
│   └── trading.html     # 交易主页面
├── static/              # 静态资源
│   ├── css/            # 样式文件
│   ├── js/             # JavaScript文件
│   └── fonts/          # 字体文件
└── logs/               # 日志文件目录
```

## 安装部署

### 环境要求
- Python 3.8-3.11
- QMT交易终端（已安装并配置）
- Windows操作系统（推荐）

### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd qmt_trader_http_server
```

2. **创建虚拟环境**
```bash
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **配置QMT路径**
编辑 `app.py` 文件，修改QMT安装路径：
```python
traders = [
    MyTradeAPIWrapper("你的账户ID", 1001, "账户名称", 
                     qmtpath=r"你的QMT安装路径\userdata_mini")
]
```

5. **配置xtquant模块**
从QMT安装目录复制xtquant相关文件到Python环境中，或按照QMT官方文档配置。

6. **启动应用**
```bash
python app.py
```

7. **访问系统**
打开浏览器访问：http://localhost:9091

## 使用说明

### 登录系统
- 默认账户：
  - 用户名：`admin` 密码：`zizai123`
  - 用户名：`trader` 密码：`zizai123`

### 主要操作
1. **查看持仓**：登录后自动显示当前持仓信息
2. **监控资产**：实时查看总资产、可用资金、盈亏情况
3. **执行交易**：通过API接口进行买卖操作
4. **日志查看**：系统自动记录所有操作日志

### API接口

#### 获取账户列表
```
GET /qmt/trade/api/accounts
```

#### 获取资产组合
```
GET /qmt/trade/api/portfolio/{trader_index}
```

#### 获取持仓信息
```
GET /qmt/trade/api/positions/{trader_index}
```

#### 执行交易
```
POST /qmt/trade/api/trade
Content-Type: application/json

{
    "action": "buy",
    "symbol": "000001",
    "price": 10.50,
    "quantity": 1000,
    "trader_index": 0
}
```

## 配置说明

### 登录账户配置
在 `app.py` 中修改 `USERS` 字典：
```python
USERS = {
    'your_username': 'your_password',
    'trader': 'trader_password'
}
```

### 日志配置
- 日志文件保存在 `logs/` 目录
- 按日期自动分割日志文件
- 支持控制台和文件双重输出

### QMT连接配置
- 确保QMT交易终端正常运行
- 配置正确的账户ID和安装路径
- 检查xtquant模块是否正确安装

## 注意事项

### 安全提醒
- 🔒 请及时修改默认登录密码
- 🔒 生产环境请使用HTTPS
- 🔒 定期备份重要数据
- 🔒 不要在公网直接暴露系统

### 使用限制
- 📋 需要有效的QMT交易账户
- 📋 仅支持A股市场交易
- 📋 需要QMT交易终端保持运行状态
- 📋 建议在交易时间内使用

### 故障排除
1. **连接失败**：检查QMT终端是否运行，路径是否正确
2. **登录问题**：确认用户名密码，检查session配置
3. **数据异常**：查看日志文件，检查API调用状态
4. **界面问题**：清除浏览器缓存，检查静态资源

## 开发说明

### 开发环境
```bash
# 启用调试模式
export FLASK_ENV=development
python app.py
```

### 代码结构
- `app.py`：主应用入口，路由配置
- `qmt_trade.py`：QMT交易接口封装类
- `trade_routes.py`：交易相关API路由
- `qmt_data.py`：市场数据获取
- `symbol_util.py`：股票代码处理工具

### 扩展开发
- 添加新的交易策略
- 扩展数据分析功能
- 集成更多市场数据源
- 优化用户界面体验

## 版本历史

- **v1.0.0**：基础交易功能实现
- **v1.1.0**：添加用户认证系统
- **v1.2.0**：优化盈亏计算逻辑
- **v1.3.0**：完善Web界面和API
- **v1.4.0**：API新增和问题修复

## 许可证

本项目仅供学习和研究使用，请遵守相关法律法规和交易所规定。

## 联系方式

如有问题或建议，请通过以下方式联系：
- 🔗 website: [https://www.zizizaizai.com/contact]
- 💬 Issues: [GitHub Issues]

---

**免责声明**：本系统仅为技术演示，实际交易请谨慎操作，风险自负。