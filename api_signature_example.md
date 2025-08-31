# QMT交易系统 - HMAC签名验证API调用示例

## 概述

为了提高API安全性，QMT交易系统的第三方接口现在使用HMAC-SHA256签名验证，替代了原来的明文API密钥传输方式。

## 签名验证流程

### 1. 请求头参数

调用API时需要在请求头中包含以下参数：

- `X-Client-ID`: 客户端标识符
- `X-Timestamp`: Unix时间戳（秒）
- `X-Signature`: HMAC-SHA256签名

### 2. 客户端配置

目前预设的客户端配置：

```
qmt_client_001 -> qmt_secret_key_2024_v1
outer_client_002 -> qmt_secret_key_zzzz
```

### 3. 签名生成步骤

#### 步骤1：构建签名字符串

签名字符串格式：
```
METHOD\nPATH\nQUERY_STRING\nBODY\nTIMESTAMP\nCLIENT_ID
```

- `METHOD`: HTTP方法（如POST）
- `PATH`: 请求路径（如/qmt/trade/api/outer/trade）
- `QUERY_STRING`: URL查询参数（如果没有则为空字符串）
- `BODY`: JSON请求体（按key排序，无空格）
- `TIMESTAMP`: Unix时间戳
- `CLIENT_ID`: 客户端ID

#### 步骤2：计算HMAC-SHA256签名

使用客户端密钥对签名字符串进行HMAC-SHA256加密，得到十六进制签名。

## 可用的外部交易接口

### 1. 单笔交易接口

**接口地址**: `POST /qmt/trade/api/outer/trade/<operation>`

**路径参数**:
- `operation` (string): 操作类型，必须是 `buy` 或 `sell`

**请求参数**:
- `trader_index` (int): 交易器索引（0开始）
- `symbol` (string): 股票代码（如"000001"）
- `trade_price` (float): 交易价格
- `position_pct` (float): 目标仓位百分比（0.1表示10%）
- `strategy_name` (string, 可选): 策略名称，默认"外部策略"

### 2. 批量交易接口

**接口地址**: `POST /qmt/trade/api/outer/trade/batch/<operation>`

**路径参数**:
- `operation` (string): 操作类型，必须是 `buy` 或 `sell`

**请求参数**:
- `symbol` (string): 股票代码
- `trade_price` (float): 交易价格
- `position_pct` (float): 目标仓位百分比（0.1表示10%）
- `strategy_name` (string, 可选): 策略名称，默认"外部策略"

## Python调用示例

```python
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

def call_outer_trade_api(operation='buy'):
    """调用第三方单笔交易API示例"""
    # 配置信息
    base_url = "http://localhost:5000"
    client_id = "outer_client_002"
    secret_key = "qmt_secret_key_zzzz"
    
    # 请求参数
    method = "POST"
    path = f"/qmt/trade/api/outer/trade/{operation}"
    query_string = ""  # 没有查询参数
    
    # 请求体
    data = {
        "trader_index": 0,
        "symbol": "000001",
        "trade_price": 10.50,
        "position_pct": 0.1,  # 10%仓位
        "strategy_name": "外部策略"
    }
    body = json.dumps(data, sort_keys=True, separators=(',', ':'))
    
    # 生成时间戳
    timestamp = str(int(time.time()))
    
    # 生成签名
    signature = generate_signature(method, path, query_string, body, timestamp, client_id, secret_key)
    
    # 构建请求头
    headers = {
        'Content-Type': 'application/json',
        'X-Client-ID': client_id,
        'X-Timestamp': timestamp,
        'X-Signature': signature
    }
    
    # 发送请求
    url = f"{base_url}{path}"
    response = requests.post(url, headers=headers, json=data)
    
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.json()}")
    
    return response

def call_outer_trade_batch_api(operation='buy'):
    """调用第三方批量交易API示例"""
    # 配置信息
    base_url = "http://localhost:5000"
    client_id = "outer_client_002"
    secret_key = "qmt_secret_key_zzzz"
    
    # 请求参数
    method = "POST"
    path = f"/qmt/trade/api/outer/trade/batch/{operation}"
    query_string = ""  # 没有查询参数
    
    # 请求体
    data = {
        "symbol": "000001",
        "trade_price": 10.50,
        "position_pct": 0.1,  # 10%仓位
        "strategy_name": "外部批量策略"
    }
    body = json.dumps(data, sort_keys=True, separators=(',', ':'))
    
    # 生成时间戳
    timestamp = str(int(time.time()))
    
    # 生成签名
    signature = generate_signature(method, path, query_string, body, timestamp, client_id, secret_key)
    
    # 构建请求头
    headers = {
        'Content-Type': 'application/json',
        'X-Client-ID': client_id,
        'X-Timestamp': timestamp,
        'X-Signature': signature
    }
    
    # 发送请求
    url = f"{base_url}{path}"
    response = requests.post(url, headers=headers, json=data)
    
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.json()}")
    
    return response

if __name__ == "__main__":
    # 测试单笔交易
    print("=== 单笔交易测试 ===")
    call_outer_trade_api()
    
    # 测试批量交易
    print("\n=== 批量交易测试 ===")
    call_outer_trade_batch_api()
```

## JavaScript调用示例

```javascript
const crypto = require('crypto');

function generateSignature(method, path, queryString, body, timestamp, clientId, secretKey) {
    // 构建签名字符串
    const signString = `${method}\n${path}\n${queryString}\n${body}\n${timestamp}\n${clientId}`;
    
    // 计算HMAC-SHA256签名
    const signature = crypto
        .createHmac('sha256', secretKey)
        .update(signString)
        .digest('hex');
    
    return signature;
}

async function callOuterTradeApi(operation = 'buy') {
    // 配置信息
    const baseUrl = "http://localhost:5000";
    const clientId = "outer_client_002";
    const secretKey = "qmt_secret_key_zzzz";
    
    // 请求参数
    const method = "POST";
    const path = `/qmt/trade/api/outer/trade/${operation}`;
    const queryString = "";  // 没有查询参数
    
    // 请求体
    const data = {
        trader_index: 0,
        symbol: "000001",
        trade_price: 10.50,
        position_pct: 0.1,  // 10%仓位
        strategy_name: "外部策略"
    };
    const body = JSON.stringify(data, Object.keys(data).sort());
    
    // 生成时间戳
    const timestamp = Math.floor(Date.now() / 1000).toString();
    
    // 生成签名
    const signature = generateSignature(method, path, queryString, body, timestamp, clientId, secretKey);
    
    // 构建请求头
    const headers = {
        'Content-Type': 'application/json',
        'X-Client-ID': clientId,
        'X-Timestamp': timestamp,
        'X-Signature': signature
    };
    
    // 发送请求
    const url = `${baseUrl}${path}`;
    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: headers,
            body: body
        });
        
        const result = await response.json();
        console.log(`状态码: ${response.status}`);
        console.log(`响应:`, result);
        
        return result;
    } catch (error) {
        console.error('请求失败:', error);
    }
}

async function callOuterTradeBatchApi(operation = 'buy') {
    // 配置信息
    const baseUrl = "http://localhost:5000";
    const clientId = "outer_client_002";
    const secretKey = "qmt_secret_key_zzzz";
    
    // 请求参数
    const method = "POST";
    const path = `/qmt/trade/api/outer/trade/batch/${operation}`;
    const queryString = "";  // 没有查询参数
    
    // 请求体
    const data = {
        symbol: "000001",
        trade_price: 10.50,
        position_pct: 0.1,  // 10%仓位
        strategy_name: "外部批量策略"
    };
    const body = JSON.stringify(data, Object.keys(data).sort());
    
    // 生成时间戳
    const timestamp = Math.floor(Date.now() / 1000).toString();
    
    // 生成签名
    const signature = generateSignature(method, path, queryString, body, timestamp, clientId, secretKey);
    
    // 构建请求头
    const headers = {
        'Content-Type': 'application/json',
        'X-Client-ID': clientId,
        'X-Timestamp': timestamp,
        'X-Signature': signature
    };
    
    // 发送请求
    const url = `${baseUrl}${path}`;
    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: headers,
            body: body
        });
        
        const result = await response.json();
        console.log(`状态码: ${response.status}`);
        console.log(`响应:`, result);
        
        return result;
    } catch (error) {
        console.error('请求失败:', error);
    }
}

// 测试调用
async function main() {
    console.log('=== 单笔交易测试 ===');
    await callOuterTradeApi();
    
    console.log('\n=== 批量交易测试 ===');
    await callOuterTradeBatchApi();
}

main();
```

## 安全特性

1. **时间戳验证**: 防止重放攻击，请求时间戳与服务器时间差不能超过5分钟
2. **HMAC签名**: 使用密钥对请求内容进行签名，确保请求完整性和身份验证
3. **密钥保护**: 密钥不在网络中传输，只用于本地签名计算
4. **请求完整性**: 签名包含HTTP方法、路径、参数、请求体等完整信息

## 错误处理

可能的错误响应：

- `缺少必要的签名验证参数` (401): 缺少X-Client-ID、X-Timestamp或X-Signature
- `请求时间戳过期` (401): 时间戳与服务器时间差超过5分钟
- `无效的时间戳格式` (401): 时间戳格式不正确
- `无效的客户端ID` (401): 客户端ID不存在
- `签名验证失败` (401): HMAC签名不匹配

## 注意事项

1. 确保客户端和服务器时间同步
2. 妥善保管客户端密钥，不要在代码中硬编码
3. 建议使用HTTPS协议传输
4. 定期更换客户端密钥