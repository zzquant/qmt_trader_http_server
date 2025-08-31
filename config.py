# -*- coding: utf-8 -*-
"""
QMT交易系统统一配置文件

该文件包含了系统的所有配置项，包括：
- Flask应用配置
- 用户认证配置
- 交易账户配置
- 日志配置
- QMT路径配置
- 服务器配置
"""

import os
from datetime import timedelta
from typing import Dict, List, Any
from dataclasses import dataclass, field


@dataclass
class TraderConfig:
    """交易账户配置"""
    account_id: str
    account_type: int
    account_name: str
    qmt_path: str
    enabled: bool = True


@dataclass
class LogConfig:
    """日志配置"""
    level: str = 'INFO'
    format: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    log_dir: str = 'logs'
    file_encoding: str = 'utf-8'
    console_output: bool = True
    file_output: bool = True
    
    def get_log_file_path(self) -> str:
        """获取日志文件路径"""
        from datetime import datetime
        return os.path.join(self.log_dir, f'app_{datetime.now().strftime("%Y%m%d")}.log')


@dataclass
class FlaskConfig:
    """Flask应用配置"""
    secret_key: str = 'qmt_trader_secret_key_2024'
    json_as_ascii: bool = False
    permanent_session_lifetime_days: int = 180
    debug: bool = True
    host: str = '0.0.0.0'
    port: int = 9091


@dataclass
class AuthConfig:
    """用户认证配置"""
    users: Dict[str, str] = None
    
    def __post_init__(self):
        if self.users is None:
            self.users = {
                'admin': 'zizai123',
                'trader': 'zizai123'
            }


@dataclass
class APIConfig:
    """API配置"""
    # HMAC签名验证配置
    signature_timeout: int = 300  # 签名超时时间（秒），默认5分钟
    client_secrets: Dict[str, str] = field(default_factory=lambda: {
        'qmt_client_001': 'qmt_secret_key_zzzz',
        'outer_client_002': 'qmt_secret_key_zzzz'
    })
    
    def is_valid_client(self, client_id: str) -> bool:
        """检查客户端ID是否有效"""
        return client_id in self.client_secrets
    
    def get_client_secret(self, client_id: str) -> str:
        """获取客户端密钥"""
        return self.client_secrets.get(client_id, '')


class Config:
    """主配置类"""
    
    def __init__(self):
        # Flask配置
        self.flask = FlaskConfig()
        
        # 用户认证配置
        self.auth = AuthConfig()
        
        # 日志配置
        self.log = LogConfig()
        
        # API配置
        self.api = APIConfig(
            signature_timeout=int(os.getenv('API_SIGNATURE_TIMEOUT', '300')),
            client_secrets={
                'qmt_client_001': os.getenv('QMT_CLIENT_001_SECRET', 'qmt_secret_key_zzzz'),
                'outer_client_002': os.getenv('OUTER_CLIENT_002_SECRET', 'qmt_secret_key_zzzz')
            }
        )
        
        # 交易账户配置
        self.traders = [
            TraderConfig(
                account_id="99007036",
                account_type=1001,
                account_name="账户1",
                qmt_path=r"D:\迅投极速策略交易系统交易终端 大同证券QMT实盘\userdata_mini",
                enabled=True
            ),
            # 可以添加更多账户
            # TraderConfig(
            #     account_id="38800001476301",
            #     account_type=1001,
            #     account_name="账户2",
            #     qmt_path=r"D:\迅投极速策略交易系统交易终端 华鑫证券QMT实盘\userdata_mini",
            #     enabled=False
            # ),
        ]
        
        # 从环境变量覆盖配置
        self._load_from_env()
    
    def _load_from_env(self):
        """从环境变量加载配置"""
        # Flask配置
        if os.getenv('FLASK_SECRET_KEY'):
            self.flask.secret_key = os.getenv('FLASK_SECRET_KEY')
        if os.getenv('FLASK_DEBUG'):
            self.flask.debug = os.getenv('FLASK_DEBUG').lower() == 'true'
        if os.getenv('FLASK_HOST'):
            self.flask.host = os.getenv('FLASK_HOST')
        if os.getenv('FLASK_PORT'):
            self.flask.port = int(os.getenv('FLASK_PORT'))
        
        # 日志配置
        if os.getenv('LOG_LEVEL'):
            self.log.level = os.getenv('LOG_LEVEL')
        if os.getenv('LOG_DIR'):
            self.log.log_dir = os.getenv('LOG_DIR')
        
        # 用户认证配置
        if os.getenv('ADMIN_PASSWORD'):
            self.auth.users['admin'] = os.getenv('ADMIN_PASSWORD')
        if os.getenv('TRADER_PASSWORD'):
            self.auth.users['trader'] = os.getenv('TRADER_PASSWORD')
        
        # API配置
        if os.getenv('API_SIGNATURE_TIMEOUT'):
            self.api.signature_timeout = int(os.getenv('API_SIGNATURE_TIMEOUT'))
        if os.getenv('QMT_CLIENT_001_SECRET'):
            self.api.client_secrets['qmt_client_001'] = os.getenv('QMT_CLIENT_001_SECRET')
        if os.getenv('OUTER_CLIENT_002_SECRET'):
            self.api.client_secrets['outer_client_002'] = os.getenv('OUTER_CLIENT_002_SECRET')
    
    def get_flask_config(self) -> Dict[str, Any]:
        """获取Flask应用配置字典"""
        return {
            'SECRET_KEY': self.flask.secret_key,
            'JSON_AS_ASCII': self.flask.json_as_ascii,
            'PERMANENT_SESSION_LIFETIME': timedelta(days=self.flask.permanent_session_lifetime_days)
        }
    
    def get_enabled_traders(self) -> List[TraderConfig]:
        """获取启用的交易账户配置"""
        return [trader for trader in self.traders if trader.enabled]
    
    def validate_config(self) -> bool:
        """验证配置的有效性"""
        # 验证交易账户配置
        for trader in self.traders:
            if trader.enabled:
                if not trader.account_id:
                    raise ValueError(f"交易账户 {trader.account_name} 的账户ID不能为空")
                if not os.path.exists(trader.qmt_path):
                    raise ValueError(f"交易账户 {trader.account_name} 的QMT路径不存在: {trader.qmt_path}")
        
        # 验证日志目录
        if not os.path.exists(self.log.log_dir):
            os.makedirs(self.log.log_dir, exist_ok=True)
        
        return True


# 全局配置实例
_config = None


def get_config() -> Config:
    """获取全局配置实例"""
    global _config
    if _config is None:
        _config = Config()
        _config.validate_config()
    return _config


def reload_config() -> Config:
    """重新加载配置"""
    global _config
    _config = None
    return get_config()


# 兼容性配置（保持向后兼容）
class LegacyConfig:
    """兼容旧版本的配置类"""
    
    @property
    def SECRET_KEY(self):
        return get_config().flask.secret_key
    
    @property
    def DEBUG(self):
        return get_config().flask.debug
    
    @property
    def HOST(self):
        return get_config().flask.host
    
    @property
    def PORT(self):
        return get_config().flask.port
    
    @property
    def USERS(self):
        return get_config().auth.users


# 导出兼容性配置实例
legacy_config = LegacyConfig()