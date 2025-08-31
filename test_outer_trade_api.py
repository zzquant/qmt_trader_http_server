#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QMT交易系统 - 外部交易接口测试脚本
使用HMAC-SHA256签名验证
"""

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
    """调用单笔交易接口"""
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
    try:
        response = requests.post(url, headers=headers, data=body)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        return response.json()
    except Exception as e:
        print(f"请求失败: {e}")

def call_outer_trade_batch_api(operation='buy'):
    """调用批量交易接口"""
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
    try:
        response = requests.post(url, headers=headers, data=body)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        return response.json()
    except Exception as e:
        print(f"请求失败: {e}")

def test_different_operations():
    """测试不同的操作类型"""
    print("\n=== 测试不同操作类型 ===")
    
    operations = ['buy', 'sell']
    
    for operation in operations:
        print(f"\n--- 测试 {operation} 操作 ---")
        call_outer_trade_api(operation)
        
        print(f"\n--- 测试批量 {operation} 操作 ---")
        call_outer_trade_batch_api(operation)

def test_invalid_signature():
    """测试无效签名"""
    print("\n=== 测试无效签名 ===")
    
    # 配置信息
    base_url = "http://localhost:5000"
    client_id = "outer_client_002"
    secret_key = "wrong_secret_key"  # 故意使用错误的密钥
    
    # 请求参数
    method = "POST"
    path = "/qmt/trade/api/outer/trade/buy"
    query_string = ""
    
    # 请求体
    data = {
        "trader_index": 0,
        "symbol": "000001",
        "trade_price": 10.50,
        "position_pct": 0.1,
        "strategy_name": "测试无效签名"
    }
    body = json.dumps(data, sort_keys=True, separators=(',', ':'))
    
    # 生成时间戳
    timestamp = str(int(time.time()))
    
    # 生成签名（使用错误的密钥）
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
    try:
        response = requests.post(url, headers=headers, data=body)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
    except Exception as e:
        print(f"请求失败: {e}")

if __name__ == "__main__":
    print("=== 外部交易API测试 ===")
    
    print("\n1. 测试单笔买入交易")
    call_outer_trade_api('buy')
    
    print("\n2. 测试单笔卖出交易")
    call_outer_trade_api('sell')
    
    print("\n3. 测试批量买入交易")
    call_outer_trade_batch_api('buy')
    
    print("\n4. 测试批量卖出交易")
    call_outer_trade_batch_api('sell')
    
    print("\n5. 测试不同操作类型")
    test_different_operations()
    
    print("\n6. 测试无效签名")
    test_invalid_signature()