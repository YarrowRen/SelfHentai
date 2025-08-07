# app/core/logger.py

import logging
import os
import sys
from functools import lru_cache

from core.config import settings


@lru_cache()
def get_logger(name: str = __name__) -> logging.Logger:
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger  # 避免重复添加 handler

    logger.setLevel(settings.LOG_LEVEL)

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 控制台输出
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    # 确保 logs 目录存在
    os.makedirs(settings.LOG_DIR, exist_ok=True)

    # 写入文件
    file_path = os.path.join(settings.LOG_DIR, settings.LOG_FILE)
    file_handler = logging.FileHandler(file_path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
