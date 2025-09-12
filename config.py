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
import json
import os
from datetime import timedelta
from typing import Dict, List, Any
from dataclasses import dataclass, field
from pathlib import Path

# 尝试加载.env文件
try:
    from dotenv import load_dotenv
    env_file_path = Path(__file__).parent / '.env'
    if env_file_path.exists():
        load_dotenv(env_file_path)
except ImportError:
    # 如果没有安装python-dotenv，手动加载.env文件
    env_file_path = Path(__file__).parent / '.env'
    if env_file_path.exists():
        with open(env_file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value


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


@dataclass
class DingBotConfig:
    access_token: str = os.getenv('DINGTALK_ACCESS_TOKEN', '')
    secret: str = os.getenv('DINGTALK_SECRET', '')
    keyword: str = os.getenv('DINGTALK_KEYWORD', '')


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
                os.getenv('QMT_CLIENT_ACCOUNT', 'qmt_client_001'): os.getenv('QMT_CLIENT_SECRET', 'qmt_secret_key_zzzz'),
                os.getenv('OUTER_CLIENT_ACCOUNT', 'outer_client_002'): os.getenv('OUTER_CLIENT_SECRET', 'qmt_secret_key_zzzz')
            }
        )
        
        # 交易账户配置
        self.traders = [TraderConfig(**cfg) for cfg in eval(os.getenv("TRADER_CONFIGS", "[]"))]

        # 钉钉机器人配置
        self.dingtalk = DingBotConfig()

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
    return _config

def save_config_to_env_file(config: Config) -> bool:
    """保存配置到.env文件
    
    将当前内存中的配置保存到.env文件中，覆盖默认配置。
    这种方式更安全，不会修改源代码文件。
    """
    import os
    from pathlib import Path
    
    env_file_path = Path(__file__).parent / '.env'
    
    try:
        # 构建.env文件内容
        env_content = "# QMT交易系统环境变量配置文件\n"
        env_content += "# 此文件由配置管理界面自动生成和更新\n\n"
        
        # Flask应用配置
        env_content += "# Flask应用配置\n"
        env_content += f"FLASK_SECRET_KEY={config.flask.secret_key}\n"
        env_content += f"FLASK_DEBUG={str(config.flask.debug).lower()}\n"
        env_content += f"FLASK_HOST={config.flask.host}\n"
        env_content += f"FLASK_PORT={config.flask.port}\n\n"
        
        # 用户认证配置
        env_content += "# 用户认证配置\n"
        for username, password in config.auth.users.items():
            env_var_name = f"{username.upper()}_PASSWORD"
            env_content += f"{env_var_name}={password}\n"
        env_content += "\n"
        
        # 日志配置
        env_content += "# 日志配置\n"
        env_content += f"LOG_LEVEL={config.log.level}\n"
        env_content += f"LOG_DIR={config.log.log_dir}\n\n"
        
        # API配置
        env_content += "# API配置\n"
        env_content += f"API_SIGNATURE_TIMEOUT={config.api.signature_timeout}\n"
        for client_id, secret in config.api.client_secrets.items():
            env_var_name = f"{client_id.upper().replace('_', '_')}_SECRET"
            env_content += f"{env_var_name}={secret}\n"
        
        # 写入.env文件
        with open(env_file_path, 'w', encoding='utf-8') as f:
            f.write(env_content)
        
        return True
        
    except Exception as e:
        raise e


def save_config_to_file(config: Config) -> bool:
    """保存配置到文件
    
    注意：这个函数会将当前内存中的配置写入到config.py文件中，
    但只会更新可以通过环境变量覆盖的配置项。
    交易账户等复杂配置仍需要手动修改config.py文件。
    """
    import tempfile
    import shutil
    
    # 创建配置文件内容
    config_content = f'''# -*- coding: utf-8 -*-
"""
QMT交易系统统一配置文件

该文件包含了系统的所有配置项，包括：
- Flask应用配置
- 用户认证配置
- 交易账户配置
- 日志配置
- QMT路径配置
- 服务器配置

注意：此文件由配置管理界面自动生成，手动修改可能会被覆盖。
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
    level: str = "{config.log.level}"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_dir: str = "{config.log.log_dir}"
    file_encoding: str = "utf-8"
    console_output: bool = {str(config.log.console_output).lower()}
    file_output: bool = {str(config.log.file_output).lower()}
    
    def get_log_file_path(self) -> str:
        """获取日志文件路径"""
        from datetime import datetime
        return os.path.join(self.log_dir, f'app_{{datetime.now().strftime("%Y%m%d")}}.log')


@dataclass
class FlaskConfig:
    """Flask应用配置"""
    secret_key: str = 'qmt_trader_secret_key_2024'
    json_as_ascii: bool = False
    permanent_session_lifetime_days: int = {config.flask.permanent_session_lifetime_days}
    debug: bool = {str(config.flask.debug).lower()}
    host: str = "{config.flask.host}"
    port: int = {config.flask.port}


@dataclass
class AuthConfig:
    """用户认证配置"""
    users: Dict[str, str] = None
    
    def __post_init__(self):
        if self.users is None:
            self.users = {{
'''
    
    # 添加用户配置
    for username, password in config.auth.users.items():
        config_content += f'                "{username}": "{password}",\n'
    
    config_content += '''            }


@dataclass
class APIConfig:
    """API配置"""
    # HMAC签名验证配置
    signature_timeout: int = ''' + str(config.api.signature_timeout) + '''  # 签名超时时间（秒）
    client_secrets: Dict[str, str] = field(default_factory=lambda: {
'''
    
    # 添加API密钥配置
    for client_id, secret in config.api.client_secrets.items():
        config_content += f'        "{client_id}": "{secret}",\n'
    
    config_content += '''    })
    
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
            client_secrets={{
'''
    
    # 添加环境变量配置
    for client_id in config.api.client_secrets.keys():
        env_var = client_id.upper().replace('_', '_') + '_SECRET'
        config_content += f'                "{client_id}": os.getenv("{env_var}", "{config.api.client_secrets[client_id]}"),\n'
    
    config_content += '''            }}
        )
        
        # 交易账户配置
        self.traders = [
'''
    
    # 添加交易账户配置（保持原有配置）
    for trader in config.traders:
        config_content += f'''            TraderConfig(
                account_id="{trader.account_id}",
                account_type={trader.account_type},
                account_name="{trader.account_name}",
                qmt_path=r"{trader.qmt_path}",
                enabled={str(trader.enabled)}
            ),
'''
    
    config_content += '''        ]
        
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
        return {{
            'SECRET_KEY': self.flask.secret_key,
            'JSON_AS_ASCII': self.flask.json_as_ascii,
            'PERMANENT_SESSION_LIFETIME': timedelta(days=self.flask.permanent_session_lifetime_days)
        }}
    
    def get_enabled_traders(self) -> List[TraderConfig]:
        """获取启用的交易账户配置"""
        return [trader for trader in self.traders if trader.enabled]
    
    def validate_config(self) -> bool:
        """验证配置的有效性"""
        # 验证交易账户配置
        for trader in self.traders:
            if trader.enabled:
                if not trader.account_id:
                    raise ValueError(f"交易账户 {{trader.account_name}} 的账户ID不能为空")
                if not os.path.exists(trader.qmt_path):
                    raise ValueError(f"交易账户 {{trader.account_name}} 的QMT路径不存在: {{trader.qmt_path}}")
        
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
    return _config
'''
    
    # 写入临时文件
    config_file_path = os.path.join(os.path.dirname(__file__), 'config.py')
    temp_file_path = config_file_path + '.tmp'
    
    try:
        with open(temp_file_path, 'w', encoding='utf-8') as f:
            f.write(config_content)
        
        # 备份原文件
        backup_path = config_file_path + '.backup'
        if os.path.exists(config_file_path):
            shutil.copy2(config_file_path, backup_path)
        
        # 替换原文件
        shutil.move(temp_file_path, config_file_path)
        
        return True
        
    except Exception as e:
        # 如果出错，删除临时文件
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        raise e


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