# utils/logger.py
"""
高级日志记录模块
提供灵活配置的日志记录功能，支持文件轮转、不同日志级别和格式化
"""

import logging
import os
import sys  # 添加这行导入语句
from logging.handlers import RotatingFileHandler
from datetime import datetime

def setup_logging(log_dir: str = "logs", log_level: str = "INFO", max_bytes: int = 5*1024*1024, backup_count: int = 5):
    """
    配置全局日志记录系统
    
    :param log_dir: 日志目录路径
    :param log_level: 日志级别（DEBUG, INFO, WARNING, ERROR, CRITICAL）
    :param max_bytes: 单个日志文件最大字节数
    :param backup_count: 保留的备份日志文件数
    """
    # 确保日志目录存在
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 设置日志文件名（带日期）
    log_filename = datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".log"
    log_path = os.path.join(log_dir, log_filename)
    
    # 创建根记录器
    logger = logging.getLogger()
    logger.setLevel(log_level.upper())
    
    # 清除现有处理器
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # 创建文件处理器（带轮转）
    file_handler = RotatingFileHandler(
        log_path, 
        maxBytes=max_bytes, 
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(log_level.upper())
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level.upper())
    
    # 创建格式化器
    formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] [%(name)s] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 应用格式化器
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # 添加处理器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # 捕获未处理异常
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            # 不捕获键盘中断
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        logger.critical("未捕获的异常", exc_info=(exc_type, exc_value, exc_traceback))
    
    sys.excepthook = handle_exception
    
    return logger

def get_logger(name: str) -> logging.Logger:
    """
    获取具有指定名称的记录器
    
    :param name: 记录器名称
    :return: 配置好的记录器实例
    """
    return logging.getLogger(name)

# 测试日志功能
if __name__ == "__main__":
    import logging
    logger = setup_logging(log_level="DEBUG")
    test_logger = get_logger("TestLogger")
    
    test_logger.debug("调试信息")
    test_logger.info("一般信息")
    test_logger.warning("警告信息")
    test_logger.error("错误信息")
    test_logger.critical("严重错误")
    
    try:
        1 / 0
    except Exception:
        test_logger.exception("异常示例")