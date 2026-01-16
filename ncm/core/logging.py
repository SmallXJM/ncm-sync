"""Logging configuration for NCM API."""

import logging
import logging.config
from typing import Optional

_LOGGING_INITIALIZED = False


def setup_logging(level: int = logging.INFO) -> None:
    global _LOGGING_INITIALIZED
    if _LOGGING_INITIALIZED:
        return

    other_level = "DEBUG" if level == logging.DEBUG else "WARNING"
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "stream": "ext://sys.stdout",
            },
        },
        "root": {
            "handlers": ["console"],
            "level": "INFO" if level == logging.DEBUG else "WARNING",
        },
        "loggers": {
            # ncm 自定义 日志等级
            "ncm": {
                "level": level,
                "propagate": True,
            },

            # --- 压制第三方 ---
            # --- uvicorn 只保留必要信息 ---
            "uvicorn": {"level": other_level},
            "uvicorn.error": {"level": other_level},  # 启动/异常还能看到
            "uvicorn.access": {
                "level": other_level,
                "propagate": False,
            },

            "httpx": {"level": other_level},
            "apscheduler": {"level": other_level},
            "watchfiles": {"level": other_level},
            "aiosqlite": {"level": "INFO" if level == logging.DEBUG else "WARNING"},
        },
    }

    logging.config.dictConfig(config)
    _LOGGING_INITIALIZED = True


def get_logger(name: Optional[str] = None) -> logging.Logger:
    return logging.getLogger(name or __name__)
