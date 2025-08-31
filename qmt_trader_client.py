#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QMT交易客户端
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


def call_buy(symbol,trade_price,position_pct=0.1,strategy_name="JQ_Q1"):
    return call_trade(symbol,trade_price,position_pct,'buy',strategy_name)

def call_sell(symbol,trade_price,position_pct=0.1,strategy_name="JQ_Q1"):
    return call_trade(symbol,trade_price,position_pct,'sell',strategy_name)

def call_trade(symbol,trade_price,position_pct=0.1,operation='buy',strategy_name="JQ_Q1"):
    """调用批量交易接口"""
    # 配置信息
    base_url = "http://yourip:9091"
    client_id = "outer_client_002"
    secret_key = "qmt_secret_key_zzzz"
    
    # 请求参数
    method = "POST"
    path = f"/qmt/trade/api/outer/trade/batch/{operation}"
    query_string = ""  # 没有查询参数
    
    # 请求体
    data = {
        "symbol": symbol[:6], # 标的
        "trade_price": trade_price, # 交易价格
        "position_pct": position_pct,  # 仓位
        "strategy_name": strategy_name # 策略名称，自定义
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
        
