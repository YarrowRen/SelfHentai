# app/core/logger.py

import logging
import os
import sys
from functools import lru_cache

from core.config import settings


class ColoredFormatter(logging.Formatter):
    """带颜色的日志格式化器"""
    
    # ANSI 颜色代码
    COLORS = {
        'DEBUG': '\033[36m',     # 青色
        'INFO': '\033[32m',      # 绿色
        'WARNING': '\033[33m',   # 黄色
        'ERROR': '\033[31m',     # 红色
        'CRITICAL': '\033[35m',  # 紫色
    }
    RESET = '\033[0m'            # 重置颜色
    
    def format(self, record):
        # 获取原始格式化结果
        log_message = super().format(record)
        
        # 检查是否应该添加颜色（只在终端输出时添加）
        if hasattr(record, 'no_color') or not self._should_use_color():
            return log_message
            
        # 添加颜色
        level_color = self.COLORS.get(record.levelname, '')
        if level_color:
            # 给级别名称添加颜色（新格式：levelname: 开头）
            colored_level = f"{level_color}{record.levelname}{self.RESET}"
            log_message = log_message.replace(f"{record.levelname}:", f"{colored_level}:")
        
        return log_message
    
    def _should_use_color(self):
        """判断是否应该使用颜色"""
        # 检查环境变量
        if os.getenv('NO_COLOR'):
            return False
        if os.getenv('FORCE_COLOR'):
            return True
        
        # 默认启用颜色（因为大多数现代终端都支持颜色）
        return True


@lru_cache()
def get_logger(name: str = __name__) -> logging.Logger:
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger  # 避免重复添加 handler

    logger.setLevel(settings.LOG_LEVEL)

    # 控制台彩色格式化器（类似uvicorn风格，保留完整日期）
    colored_formatter = ColoredFormatter(
        "%(levelname)s:    [%(asctime)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 文件普通格式化器（保留完整时间戳）
    file_formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 控制台输出（使用stderr以获得终端颜色支持）
    stream_handler = logging.StreamHandler(sys.stderr)
    stream_handler.setFormatter(colored_formatter)
    logger.addHandler(stream_handler)

    # 确保 logs 目录存在
    os.makedirs(settings.LOG_DIR, exist_ok=True)

    # 写入文件
    file_path = os.path.join(settings.LOG_DIR, settings.LOG_FILE)
    file_handler = logging.FileHandler(file_path, encoding="utf-8")
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    return logger
