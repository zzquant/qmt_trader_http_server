# 配置管理说明

本项目已将所有配置统一到 `config.py` 文件中，提供了更好的配置管理和环境变量支持。

## 配置文件结构

### 主配置文件：`config.py`

包含以下配置模块：

1. **FlaskConfig** - Flask应用配置
   - `secret_key`: 会话加密密钥
   - `json_as_ascii`: JSON响应编码设置
   - `permanent_session_lifetime_days`: 会话有效期（天）
   - `debug`: 调试模式
   - `host`: 服务器监听地址
   - `port`: 服务器端口

2. **AuthConfig** - 用户认证配置
   - `users`: 用户名密码字典

3. **LogConfig** - 日志配置
   - `level`: 日志级别
   - `format`: 日志格式
   - `log_dir`: 日志目录
   - `file_encoding`: 日志文件编码
   - `console_output`: 是否输出到控制台
   - `file_output`: 是否输出到文件

4. **APIConfig** - API接口配置
   - `signature_timeout`: HMAC签名超时时间（秒）
   - `client_secrets`: 客户端密钥字典

5. **TraderConfig** - 交易账户配置
   - `account_id`: 账户ID
   - `account_type`: 账户类型
   - `account_name`: 账户名称
   - `qmt_path`: QMT安装路径
   - `enabled`: 是否启用

## 配置方式

### 1. 直接修改配置文件

编辑 `config.py` 文件中的相应配置类：

```python
# 修改Flask配置
self.flask = FlaskConfig(
    secret_key='your-new-secret-key',
    debug=False,
    port=8080
)

# 添加交易账户
self.traders = [
    TraderConfig(
        account_id="your-account-id",
        account_type=1001,
        account_name="主账户",
        qmt_path=r"D:\your-qmt-path\userdata_mini",
        enabled=True
    ),
]
```

### 2. 使用环境变量

创建 `.env` 文件（参考 `.env.example`）：

```bash
# 复制示例文件
cp .env.example .env

# 编辑配置
FLASK_SECRET_KEY=your-production-secret-key
FLASK_DEBUG=false
FLASK_PORT=8080
LOG_LEVEL=WARNING
ADMIN_PASSWORD=your-secure-password
TRADER_PASSWORD=your-trader-password
```

支持的环境变量：

- `FLASK_SECRET_KEY`: Flask密钥
- `FLASK_DEBUG`: 调试模式 (true/false)
- `FLASK_HOST`: 监听地址
- `FLASK_PORT`: 监听端口
- `LOG_LEVEL`: 日志级别 (DEBUG/INFO/WARNING/ERROR)
- `LOG_DIR`: 日志目录
- `ADMIN_PASSWORD`: 管理员密码
- `TRADER_PASSWORD`: 交易员密码
- `API_SIGNATURE_TIMEOUT`: API签名超时时间（秒）
- `QMT_CLIENT_001_SECRET`: QMT客户端001的密钥
- `OUTER_CLIENT_002_SECRET`: 外部客户端002的密钥

## 配置优先级

1. 环境变量（最高优先级）
2. 配置文件中的设置
3. 默认值（最低优先级）

## 使用方法

### 在代码中获取配置

```python
from config import get_config

# 获取配置实例
config = get_config()

# 使用配置
app.config.update(config.get_flask_config())
users = config.auth.users
traders = config.get_enabled_traders()
```

### 配置验证

系统会自动验证配置的有效性：

- 检查QMT路径是否存在
- 验证必要的配置项是否为空
- 自动创建日志目录

## 迁移指南

### 从旧版本迁移

1. **备份现有配置**
   ```bash
   # 备份当前的app.py文件
   cp app.py app.py.backup
   ```

2. **更新配置**
   - 将原来在 `app.py` 中的硬编码配置移动到 `config.py`
   - 更新QMT路径和账户信息
   - 设置用户密码

3. **测试配置**
   ```bash
   python -c "from config import get_config; config = get_config(); print('配置加载成功')"
   ```

### 兼容性

为了保持向后兼容，提供了 `LegacyConfig` 类，但建议尽快迁移到新的配置系统。

## 安全建议

1. **生产环境**
   - 务必修改默认密码
   - 使用强密钥
   - 设置 `FLASK_DEBUG=false`
   - 使用HTTPS

2. **文件权限**
   - 确保 `.env` 文件不被提交到版本控制
   - 设置适当的文件权限

3. **密钥管理**
   - 定期更换密钥
   - 使用环境变量而非硬编码
   - 考虑使用密钥管理服务

## 故障排除

### 常见问题

1. **配置加载失败**
   ```
   ImportError: No module named 'config'
   ```
   解决：确保 `config.py` 文件在正确位置

2. **QMT路径错误**
   ```
   ValueError: QMT路径不存在
   ```
   解决：检查并更新 `config.py` 中的 `qmt_path` 设置

3. **权限问题**
   ```
   PermissionError: 无法创建日志目录
   ```
   解决：确保应用有写入权限，或手动创建日志目录

### 调试配置

```python
# 打印当前配置
from config import get_config
config = get_config()
print(f"Flask配置: {config.get_flask_config()}")
print(f"启用的交易账户: {len(config.get_enabled_traders())}")
print(f"日志级别: {config.log.level}")
```

## 更新日志

- **v1.0**: 初始版本，统一配置管理
- 支持环境变量覆盖
- 配置验证和错误处理
- 向后兼容性支持