# -*- coding: utf-8 -*-
from flask import request, jsonify, session
import hmac
import hashlib
import time
import json
from functools import wraps
from config import get_config
from logger_config import get_logger

config = get_config()
log = get_logger(__name__)


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
