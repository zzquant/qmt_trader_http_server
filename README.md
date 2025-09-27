# QMT交易HTTP服务器

基于Flask的QMT（迅投极速交易系统）HTTP API服务器，提供Web界面和RESTful API接口进行量化交易操作。

## 项目简介

本项目是一个专为QMT交易终端设计的HTTP服务器，通过Web界面和API接口实现远程交易控制。支持多账户管理、实时持仓查询、交易下单、撤单等功能，并提供完善的身份验证和日志记录机制。

## 主要功能

### Web界面功能
- **用户登录认证** - 支持管理员和交易员两种角色
- **交易界面** - 实时显示持仓、资产、交易操作
- **配置管理** - 在线配置交易参数和系统设置
- **实时数据** - 动态更新持仓和资产信息

### API接口功能
- **账户管理** - 查询交易账户信息和状态
- **持仓查询** - 获取实时持仓数据和资产组合
- **交易下单** - 支持买入、卖出、全仓买入等操作
- **订单管理** - 查询订单状态、撤单操作
- **风控功能** - 支持一键撤销买单/卖单

### 安全特性
- **双重认证** - 支持Web登录和API签名验证
- **HMAC签名** - API接口使用HMAC-SHA256签名防篡改
- **时间戳验证** - 防止重放攻击
- **多客户端支持** - 支持不同客户端的独立密钥管理

## 技术架构

- **后端框架**: Flask 2.3.3
- **交易接口**: QMT xtquant
- **数据处理**: pandas, numpy
- **前端技术**: Bootstrap 5, JavaScript
- **配置管理**: python-dotenv
- **日志系统**: Python logging
- **通知系统**: 钉钉机器人集成

## 项目结构

```
qmt_trader_http_server/
├── app.py                 # Flask应用主入口
├── config.py              # 配置管理模块
├── qmt_trade.py           # QMT交易接口封装
├── trade_routes.py        # 交易API路由
├── authentication.py     # 身份验证模块
├── logger_config.py       # 日志配置
├── dingtalk_helper.py     # 钉钉通知助手
├── symbol_util.py         # 股票代码工具
├── qmt_data.py           # QMT数据接口
├── requirements.txt       # 项目依赖
├── .env.example          # 环境变量示例
├── templates/            # HTML模板
│   ├── login.html        # 登录页面
│   ├── trading.html      # 交易界面
│   └── config.html       # 配置页面
└── static/               # 静态资源
    ├── css/              # 样式文件
    └── js/               # JavaScript文件
```

## 安装部署

### 环境要求

- Python 3.8-3.11
- QMT交易终端（已安装并配置）
- Windows操作系统（QMT要求）

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
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **配置QMT**
   - 确保QMT交易终端已正确安装
   - 从QMT安装目录获取xtquant模块
   - 配置交易账户信息

5. **环境配置**
```bash
copy .env.example .env
# 编辑.env文件，配置相关参数
```

6. **启动应用**
```bash
python app.py
```

## 配置说明

### 环境变量配置

在`.env`文件中配置以下参数：

#### Flask应用配置
```env
FLASK_SECRET_KEY=your-secret-key-here
FLASK_DEBUG=false
FLASK_HOST=0.0.0.0
FLASK_PORT=9091
```

#### 用户认证配置
```env
ADMIN_PASSWORD=your-admin-password
TRADER_PASSWORD=your-trader-password
```

#### API配置
```env
API_SIGNATURE_TIMEOUT=300
QMT_CLIENT_ACCOUNT=qmt_client_001
QMT_CLIENT_SECRET=your-qmt-client-001-secret
OUTER_CLIENT_ACCOUNT=outer_client_002
OUTER_CLIENT_SECRET=your-outer-client-002-secret
```

#### 交易账户配置 (TRADER_CONFIGS)

`TRADER_CONFIGS`是一个JSON字符串，用于配置QMT交易账户信息：

```env
TRADER_CONFIGS="[
  {
    'account_id': '3880000xxxxxx',
    'account_type': 1001,
    'account_name': '账户1',
    'qmt_path': 'C:/迅投极速策略交易系统交易终端 华鑫证券QMT实盘/userdata_mini',
    'enabled': True
  }
]"
```

**参数说明：**

| 参数 | 类型 | 说明 |
|------|------|------|
| `account_id` | string | QMT交易账户ID |
| `account_type` | int | 账户类型（1001=股票账户） |
| `account_name` | string | 账户显示名称 |
| `qmt_path` | string | QMT用户数据目录路径 |
| `enabled` | boolean | 是否启用该账户 |

**配置注意事项：**
- `qmt_path`必须指向正确的QMT用户数据目录
- 路径中的反斜杠需要使用正斜杠或双反斜杠
- 确保QMT交易终端已正确配置并能正常登录
- 建议先在QMT终端中测试账户连接

**QMT路径示例：**
```
# 华鑫证券
C:/迅投极速策略交易系统交易终端 华鑫证券QMT实盘/userdata_mini

# 其他券商类似路径格式
D:/迅投极速策略交易系统交易终端 XX证券QMT实盘/userdata_mini
```

#### 钉钉通知配置
```env
DINGTALK_ACCESS_TOKEN=your_access_token_here
DINGTALK_SECRET=your_dingtalk_secret_here
DINGTALK_KEYWORD=your_keyword_here
```

## 使用说明

### Web界面使用

1. **访问系统**
   - 浏览器访问：`http://localhost:9091`
   - 使用配置的用户名密码登录

2. **交易操作**
   - 查看实时持仓和资产信息
   - 执行买入、卖出操作
   - 管理订单和撤单

3. **配置管理**
   - 在线修改交易参数
   - 调整系统设置

### API接口使用

#### 认证方式

**方式一：Web登录**
- 先通过Web界面登录，然后可直接调用API

**方式二：HMAC签名**
- 在请求头中添加签名信息：
```
X-Client-ID: your_client_id
X-Timestamp: unix_timestamp
X-Signature: hmac_sha256_signature
```

#### 主要API接口

**账户相关**
```
GET /qmt/trade/api/accounts              # 获取所有账户信息
GET /qmt/trade/api/portfolio/{index}     # 获取指定账户资产组合
GET /qmt/trade/api/positions/{index}     # 获取指定账户持仓
```

**交易相关**
```
POST /qmt/trade/api/trade               # 普通交易下单
POST /qmt/trade/api/trade/allin         # 全仓买入
POST /qmt/trade/api/trade/nhg           # 逆回购交易
POST /qmt/trade/api/sell                # 卖出操作
```

**订单管理**
```
POST /qmt/trade/api/orders              # 查询订单
POST /qmt/trade/api/cancel_order        # 撤销指定订单
POST /qmt/trade/api/cancel_orders/buy   # 撤销所有买单
POST /qmt/trade/api/cancel_orders/sale  # 撤销所有卖单
```

**外部接口**
```
POST /qmt/trade/api/outer/trade/{operation}  # 外部交易接口
```

#### 请求示例

**买入股票**
```bash
curl -X POST http://localhost:9091/qmt/trade/api/trade \
  -H "Content-Type: application/json" \
  -H "X-Client-ID: qmt_client_001" \
  -H "X-Timestamp: 1640995200" \
  -H "X-Signature: your_signature" \
  -d '{
    "trader_index": 0,
    "symbol": "000001",
    "volume": 100,
    "price": 10.50,
    "order_type": 23
  }'
```

**查询持仓**
```bash
curl -X GET http://localhost:9091/qmt/trade/api/positions/0 \
  -H "X-Client-ID: qmt_client_001" \
  -H "X-Timestamp: 1640995200" \
  -H "X-Signature: your_signature"
```

## 注意事项

### 安全建议
- 生产环境务必修改默认密码
- 妥善保管API密钥，不要提交到版本控制
- 建议使用HTTPS部署
- 定期更新密钥和密码

### QMT配置
- 确保QMT交易终端正常运行
- 验证账户权限和交易时间
- 注意交易规则和风控限制
- 建议先在模拟环境测试

### 系统要求
- 需要Windows系统运行QMT
- 确保网络连接稳定
- 建议配置足够的系统资源
- 定期备份配置和日志

### 故障排除
- 检查QMT连接状态
- 查看日志文件排查错误
- 验证账户配置正确性
- 确认交易时间和权限

## 开发说明

### 项目架构
- 采用Flask蓝图组织路由
- 使用装饰器实现认证和异常处理
- 配置类管理所有系统参数
- 日志系统记录操作和错误

### 扩展开发
- 新增API接口在`trade_routes.py`中添加
- 修改前端界面编辑`templates/`目录文件
- 添加新功能需要相应的认证和日志
- 遵循现有的错误处理模式

### 测试建议
- 先在模拟环境测试所有功能
- 验证API接口的参数和返回值
- 测试异常情况的处理
- 确保日志记录完整

## 版本历史

- **v1.0.0** - 初始版本，基本交易功能
- **v1.1.0** - 添加Web界面和多账户支持
- **v1.2.0** - 增强安全认证和API接口
- **v1.3.0** - 优化前端界面和用户体验

## 许可证

本项目仅供学习和研究使用，请遵守相关法律法规和交易所规则。

## 联系方式
https://quant.zizizaizai.com/contact
如有问题或建议，请通过以下方式联系：
- 项目Issues
- 邮件联系
- 技术交流群

---

**免责声明**: 本软件仅供学习和研究使用，使用者需自行承担交易风险。开发者不对任何交易损失承担责任。