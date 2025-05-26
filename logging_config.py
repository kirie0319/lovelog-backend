import logging
import logging.config
import os
from datetime import datetime

def setup_logging():
    """ログ設定をセットアップ"""
    
    # ログディレクトリを作成
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # ログファイル名に日付を含める
    today = datetime.now().strftime("%Y-%m-%d")
    
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "detailed": {
                "format": "[%(asctime)s] %(levelname)s in %(name)s [%(filename)s:%(lineno)d]: %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "simple": {
                "format": "%(levelname)s - %(message)s"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "DEBUG",
                "formatter": "detailed",
                "stream": "ext://sys.stdout"
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "DEBUG",
                "formatter": "detailed",
                "filename": f"{log_dir}/app_{today}.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "detailed",
                "filename": f"{log_dir}/error_{today}.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5
            }
        },
        "loggers": {
            "": {  # root logger
                "level": "DEBUG",
                "handlers": ["console", "file", "error_file"]
            },
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console", "file"],
                "propagate": False
            },
            "uvicorn.error": {
                "level": "INFO",
                "handlers": ["console", "file", "error_file"],
                "propagate": False
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["console", "file"],
                "propagate": False
            },
            "sqlalchemy.engine": {
                "level": "INFO",
                "handlers": ["console", "file"],
                "propagate": False
            },
            "sqlalchemy.dialects": {
                "level": "DEBUG",
                "handlers": ["file"],
                "propagate": False
            },
            "fastapi": {
                "level": "DEBUG",
                "handlers": ["console", "file"],
                "propagate": False
            }
        }
    }
    
    logging.config.dictConfig(logging_config)
    
    # アプリケーション用のロガーを作成
    logger = logging.getLogger("lovelog_app")
    logger.info("Logging setup completed")
    
    return logger

def get_logger(name: str = "lovelog_app"):
    """ロガーを取得"""
    return logging.getLogger(name) 