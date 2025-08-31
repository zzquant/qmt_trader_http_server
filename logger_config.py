import logging
import os
from datetime import datetime

def setup_logging():
    """
    配置应用程序日志
    
    Returns:
        logging.Logger: 配置好的日志记录器
    """
    # 延迟导入配置，避免循环导入
    try:
        from config import get_config
        config = get_config()
        log_config = config.log
    except ImportError:
        # 如果配置文件不可用，使用默认配置
        class DefaultLogConfig:
            level = 'INFO'
            format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            log_dir = 'logs'
            file_encoding = 'utf-8'
            console_output = True
            file_output = True
            
            def get_log_file_path(self):
                return os.path.join(self.log_dir, f'app_{datetime.now().strftime("%Y%m%d")}.log')
        
        log_config = DefaultLogConfig()
    
    # 创建日志目录
    if not os.path.exists(log_config.log_dir):
        os.makedirs(log_config.log_dir)
    
    # 准备处理器列表
    handlers = []
    
    # 控制台输出
    if log_config.console_output:
        handlers.append(logging.StreamHandler())
    
    # 文件输出
    if log_config.file_output:
        handlers.append(
            logging.FileHandler(
                log_config.get_log_file_path(),
                encoding=log_config.file_encoding
            )
        )
    
    # 配置根日志记录器
    logging.basicConfig(
        level=getattr(logging, log_config.level.upper()),
        format=log_config.format,
        handlers=handlers,
        force=True  # 强制重新配置
    )
    
    return logging.getLogger(__name__)

def get_logger(name=None):
    """
    获取日志记录器
    
    Args:
        name (str, optional): 日志记录器名称，默认为调用模块名
    
    Returns:
        logging.Logger: 日志记录器
    """
    return logging.getLogger(name or __name__)