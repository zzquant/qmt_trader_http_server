import logging
import os
from datetime import datetime

def setup_logging():
    """
    配置应用程序日志
    
    Returns:
        logging.Logger: 配置好的日志记录器
    """
    # 创建logs目录
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # 设置日志格式
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # 配置根日志记录器
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            # 控制台输出
            logging.StreamHandler(),
            # 文件输出
            logging.FileHandler(
                f'logs/app_{datetime.now().strftime("%Y%m%d")}.log',
                encoding='utf-8'
            )
        ]
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