<p align="center">
  <h1 align="center">🚀 QMT Trader HTTP Server</h1>
  <p align="center">
    <strong>QMT量化交易HTTP服务 · 远程下单 · 多账户管理</strong>
  </p>
  <p align="center">
    <a href="#-快速开始">快速开始</a> •
    <a href="#-api接口">API接口</a> •
    <a href="#-python客户端">Python客户端</a> •
    <a href="#-配置说明">配置说明</a>
  </p>
</p>

---

## ✨ 特性

- 🌐 **HTTP API** - 将QMT交易能力封装为RESTful API，支持远程调用
- 👥 **多账户** - 支持配置多个QMT交易账户，统一管理
- 🔐 **安全认证** - HMAC-SHA256签名验证，防篡改防重放
- 📊 **Web界面** - 可视化交易界面，实时持仓和资产查看
- 🔔 **钉钉通知** - 交易信号自动推送到钉钉群
- 📝 **完整日志** - 所有交易操作记录在案

---

## 📦 安装

### 环境要求
- Windows 系统 (QMT仅支持Windows)
- Python 3.8 - 3.11
- QMT交易终端 (已安装配置)

### 安装步骤

```bash
# 1. 克隆项目
git clone https://github.com/yourname/qmt_trader_http_server.git
cd qmt_trader_http_server

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
copy .env.example .env
# 编辑 .env 文件，配置账户信息

# 4. 启动服务
python app.py
```

启动后访问：`http://localhost:9091`

---

## 🚀 快速开始

### 方式一：Web界面

浏览器访问 `http://localhost:9091`，登录后即可：
- 查看实时持仓和资产
- 执行买入/卖出操作
- 管理订单和撤单

### 方式二：Python客户端 (推荐)

```python
from qmt_trader_client import call_buy, call_sell

# 买入：平安银行，价格10.50，仓位10%
call_buy("000001", 10.50, 0.1, "我的策略")

# 卖出：平安银行，价格11.00，仓位50%
call_sell("000001", 11.00, 0.5, "我的策略")
```

### 方式三：HTTP API

```bash
# 查询持仓
curl http://localhost:9091/qmt/trade/api/positions/0

# 买入股票
curl -X POST http://localhost:9091/qmt/trade/api/trade \
  -H "Content-Type: application/json" \
  -d '{"trader_index": 0, "symbol": "000001", "volume": 100, "price": 10.50}'
```

---

## 🐍 Python客户端

项目提供开箱即用的Python客户端 `qmt_trader_client.py`：

```python
from qmt_trader_client import call_buy, call_sell, call_trade

# 配置 (修改 qmt_trader_client.py 中的配置)
base_url = "http://yourip:9091"
client_id = "outer_client_002"
secret_key = "your_secret_key"

# 买入
call_buy(symbol="000001", trade_price=10.50, position_pct=0.1, strategy_name="策略A")

# 卖出
call_sell(symbol="000001", trade_price=11.00, position_pct=0.5, strategy_name="策略A")

# 通用调用
call_trade(
    symbol="000001",
    trade_price=10.50,
    position_pct=0.1,
    operation='buy',  # 'buy' 或 'sell'
    strategy_name="策略A"
)
```

**参数说明：**
| 参数 | 说明 | 示例 |
|:---|:---|:---|
| `symbol` | 股票代码 | `"000001"` |
| `trade_price` | 交易价格 | `10.50` |
| `position_pct` | 仓位比例 (0.1=10%) | `0.1` |
| `operation` | 操作类型 | `"buy"` 或 `"sell"` |
| `strategy_name` | 策略名称 (自定义) | `"我的策略"` |

---

## 📡 API接口

### 账户与持仓

| 接口 | 方法 | 描述 |
|:---|:---|:---|
| `/qmt/trade/api/accounts` | GET | 获取所有账户 |
| `/qmt/trade/api/portfolio/{index}` | GET | 获取资产组合 |
| `/qmt/trade/api/positions/{index}` | GET | 获取持仓列表 |

### 交易操作

| 接口 | 方法 | 描述 |
|:---|:---|:---|
| `/qmt/trade/api/trade` | POST | 普通下单 |
| `/qmt/trade/api/trade/allin` | POST | 全仓买入 |
| `/qmt/trade/api/sell` | POST | 卖出 |

### 订单管理

| 接口 | 方法 | 描述 |
|:---|:---|:---|
| `/qmt/trade/api/orders` | POST | 查询订单 |
| `/qmt/trade/api/cancel_order` | POST | 撤销订单 |
| `/qmt/trade/api/cancel_orders/buy` | POST | 撤销所有买单 |
| `/qmt/trade/api/cancel_orders/sale` | POST | 撤销所有卖单 |

### 外部接口

| 接口 | 方法 | 描述 |
|:---|:---|:---|
| `/qmt/trade/api/outer/trade/{operation}` | POST | 外部策略调用 |

> 💡 完整API文档见 [api_signature_example.md](api_signature_example.md)

---

## ⚙️ 配置说明

编辑 `.env` 文件配置以下内容：

### 基础配置
```env
FLASK_SECRET_KEY=your-secret-key
FLASK_PORT=9091
```

### 用户认证
```env
ADMIN_PASSWORD=your-admin-password
TRADER_PASSWORD=your-trader-password
```

### API客户端
```env
QMT_CLIENT_ACCOUNT=qmt_client_001
QMT_CLIENT_SECRET=your-client-secret
```

### QMT账户配置

```env
TRADER_CONFIGS="[
  {
    'account_id': '3880000xxxxxx',
    'account_type': 1001,
    'account_name': '主账户',
    'qmt_path': 'C:/迅投极速策略交易系统交易终端 华鑫证券QMT实盘/userdata_mini',
    'enabled': True
  }
]"
```

### 钉钉通知 (可选)
```env
DINGTALK_ACCESS_TOKEN=your_token
DINGTALK_SECRET=your_secret
```

> 📖 完整配置说明见 [CONFIG.md](CONFIG.md)

---

## 🔐 API签名认证

使用HMAC-SHA256签名保证API安全：

```
请求头:
X-Client-ID: your_client_id
X-Timestamp: unix_timestamp
X-Signature: hmac_sha256_signature
```

签名规则：
```
签名字符串 = {method}\n{path}\n{query}\n{body}\n{timestamp}\n{client_id}
签名 = HMAC-SHA256(secret_key, 签名字符串)
```

> 📖 详细签名说明见 [api_signature_example.md](api_signature_example.md)

---

## ❓ 常见问题

<details>
<summary><b>Q: QMT连接失败怎么办？</b></summary>

1. 确保QMT交易终端已启动并登录
2. 检查 `qmt_path` 路径配置是否正确
3. 验证账户ID和类型配置

</details>

<details>
<summary><b>Q: API签名验证失败？</b></summary>

1. 检查 client_id 和 secret_key 是否匹配
2. 确保时间戳误差在5分钟以内
3. 验证签名字符串构建顺序

</details>

<details>
<summary><b>Q: 支持哪些券商？</b></summary>

理论上支持所有提供QMT接入的券商，已测试：
- 华鑫证券
- 其他支持QMT的券商

</details>

---

## 🛡️ 安全建议

- ⚠️ 生产环境务必修改默认密码
- ⚠️ 妥善保管API密钥，不要提交到Git
- ⚠️ 建议使用HTTPS部署
- ⚠️ 建议先在模拟环境测试

---

## 📄 License

MIT License - 仅供学习研究使用

---

<p align="center">
  ⚠️ <b>免责声明</b>：本软件仅供学习研究，使用者需自行承担交易风险。
</p>

<p align="center">
  ⭐ 如果这个项目对你有帮助，请给它一个 Star！
</p>