"""
LungFung 統一日誌配置模組

提供標準化的 Django LOGGING 配置，減少子系統重複配置。
所有子系統可以使用此模組快速配置日誌系統。

使用方法:
    from lungfung_sso import configure_logging
    
    # 在 settings.py 中
    LOGGING = configure_logging(
        base_dir=BASE_DIR,
        debug=DEBUG,
        app_log_level='DEBUG',  # 應用程式日誌級別
        system_name='APS',      # 系統代碼
    )
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List


def configure_logging(
    base_dir: Path,
    debug: bool = False,
    app_log_level: Optional[str] = None,
    django_log_level: Optional[str] = None,
    system_name: str = 'APP',
    extra_loggers: Optional[Dict[str, Dict]] = None,
    log_to_file: bool = True,
    log_dir_name: str = 'logs',
    max_bytes: int = 10485760,  # 10 MB
    backup_count: int = 10,
    include_sql_logs: bool = False,
    include_request_logs: bool = False,
) -> Dict[str, Any]:
    """
    生成標準化的 Django LOGGING 配置
    
    Args:
        base_dir: Django 專案根目錄 (BASE_DIR)
        debug: 是否為開發模式 (DEBUG)
        app_log_level: 應用程式日誌級別，預設 DEBUG(開發) / INFO(生產)
        django_log_level: Django 框架日誌級別，預設 INFO
        system_name: 系統名稱/代碼，用於日誌標識
        extra_loggers: 額外的 logger 配置
        log_to_file: 是否記錄到文件
        log_dir_name: 日誌目錄名稱
        max_bytes: 日誌文件最大大小
        backup_count: 日誌文件備份數量
        include_sql_logs: 是否包含 SQL 查詢日誌 (開發調試用)
        include_request_logs: 是否包含請求詳細日誌
        
    Returns:
        Django LOGGING 配置字典
    """
    # 設置日誌級別
    if app_log_level is None:
        app_log_level = 'DEBUG' if debug else 'INFO'
    if django_log_level is None:
        django_log_level = 'INFO'
    
    # 確保日誌目錄存在
    log_dir = Path(base_dir) / log_dir_name
    log_dir.mkdir(exist_ok=True)
    
    # 基礎 handlers 配置
    handlers = {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'colored' if debug else 'simple',
            'level': 'DEBUG',
        },
    }
    
    # 文件 handlers
    if log_to_file:
        handlers.update({
            'file_app': {
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': str(log_dir / 'app.log'),
                'maxBytes': max_bytes,
                'backupCount': backup_count,
                'formatter': 'verbose',
                'level': 'DEBUG',
                'encoding': 'utf-8',
            },
            'file_error': {
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': str(log_dir / 'error.log'),
                'maxBytes': max_bytes,
                'backupCount': backup_count,
                'formatter': 'verbose',
                'level': 'ERROR',
                'encoding': 'utf-8',
            },
        })
    
    # SQL 日誌級別
    sql_log_level = 'DEBUG' if include_sql_logs else 'WARNING'
    
    # 請求日誌級別
    request_log_level = 'DEBUG' if include_request_logs else 'WARNING'
    
    # 構建 loggers 配置
    loggers = {
        # Django 框架日誌
        'django': {
            'handlers': ['console'],
            'level': django_log_level,
            'propagate': False,
        },
        # Django 請求日誌
        'django.request': {
            'handlers': ['console'] + (['file_error'] if log_to_file else []),
            'level': request_log_level,
            'propagate': False,
        },
        # Django 數據庫日誌
        'django.db.backends': {
            'handlers': ['console'],
            'level': sql_log_level,
            'propagate': False,
        },
        # Django 模板日誌
        'django.template': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        # Django 自動重載日誌 (減少開發時的噪音)
        'django.utils.autoreload': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        # Django 安全日誌
        'django.security': {
            'handlers': ['console'] + (['file_error'] if log_to_file else []),
            'level': 'WARNING',
            'propagate': False,
        },
        # 應用程式日誌
        'apps': {
            'handlers': ['console'] + (['file_app', 'file_error'] if log_to_file else []),
            'level': app_log_level,
            'propagate': False,
        },
        # LungFung SSO 日誌
        'lungfung_sso': {
            'handlers': ['console'] + (['file_app'] if log_to_file else []),
            'level': app_log_level,
            'propagate': False,
        },
        # Celery 日誌
        'celery': {
            'handlers': ['console'] + (['file_app'] if log_to_file else []),
            'level': 'INFO',
            'propagate': False,
        },
        # HTTP 請求庫日誌
        'urllib3': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'requests': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
    }
    
    # 添加額外的 loggers
    if extra_loggers:
        loggers.update(extra_loggers)
    
    # 構建完整配置
    logging_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'verbose': {
                'format': '[{levelname}] {asctime} [{name}:{lineno}] {message}',
                'style': '{',
                'datefmt': '%Y-%m-%d %H:%M:%S',
            },
            'simple': {
                'format': '{levelname} {asctime} {name} {message}',
                'style': '{',
                'datefmt': '%Y-%m-%d %H:%M:%S',
            },
            'colored': {
                '()': 'lungfung_sso.logging_config.ColoredFormatter',
                'format': '{levelname} {asctime} {name} {message}',
                'style': '{',
                'datefmt': '%H:%M:%S',
            },
            'json': {
                '()': 'lungfung_sso.logging_config.JSONFormatter',
                'system_name': system_name,
            },
        },
        'handlers': handlers,
        'root': {
            'handlers': ['console'],
            'level': 'WARNING',
        },
        'loggers': loggers,
    }
    
    return logging_config


class ColoredFormatter(logging.Formatter):
    """
    彩色日誌格式化器 (用於開發環境)
    """
    
    # ANSI 顏色碼
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
    }
    RESET = '\033[0m'
    BOLD = '\033[1m'
    
    def format(self, record):
        # 獲取顏色
        color = self.COLORS.get(record.levelname, '')
        
        # 格式化消息
        message = super().format(record)
        
        # 添加顏色
        if color:
            # 只對 levelname 上色
            levelname = record.levelname
            colored_levelname = f"{self.BOLD}{color}{levelname}{self.RESET}"
            message = message.replace(levelname, colored_levelname, 1)
        
        return message


class JSONFormatter(logging.Formatter):
    """
    JSON 格式日誌格式化器 (用於生產環境日誌收集)
    """
    
    def __init__(self, system_name: str = 'APP', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.system_name = system_name
    
    def format(self, record):
        import json
        from datetime import datetime
        
        log_data = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'system': self.system_name,
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # 添加異常信息
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # 添加額外字段
        if hasattr(record, 'user'):
            log_data['user'] = str(record.user)
        if hasattr(record, 'request_id'):
            log_data['request_id'] = record.request_id
        if hasattr(record, 'extra_data'):
            log_data['extra'] = record.extra_data
        
        return json.dumps(log_data, ensure_ascii=False)


class RequestContextFilter(logging.Filter):
    """
    為日誌記錄添加請求上下文信息
    """
    
    def filter(self, record):
        # 嘗試獲取當前請求
        try:
            from django.conf import settings
            
            # 從線程本地存儲獲取請求信息
            request_info = getattr(self, '_request_info', {})
            record.request_id = request_info.get('request_id', '-')
            record.user = request_info.get('user', 'anonymous')
            record.ip = request_info.get('ip', '-')
        except Exception:
            record.request_id = '-'
            record.user = 'anonymous'
            record.ip = '-'
        
        return True


def get_logger(name: str) -> logging.Logger:
    """
    獲取預配置的 logger
    
    Args:
        name: logger 名稱，建議使用 'apps.{module_name}' 格式
        
    Returns:
        配置好的 logger 實例
        
    Example:
        logger = get_logger('apps.approvals')
        logger.info('Approval created', extra={'approval_id': 123})
    """
    return logging.getLogger(name)


def log_exception(logger: logging.Logger, message: str, exc: Exception, **extra):
    """
    記錄異常日誌的便捷方法
    
    Args:
        logger: logger 實例
        message: 日誌消息
        exc: 異常對象
        **extra: 額外的上下文信息
    """
    logger.exception(
        f"{message}: {exc}",
        extra={'extra_data': extra} if extra else {},
        exc_info=True
    )


def log_user_action(
    logger: logging.Logger,
    user,
    action: str,
    details: Optional[Dict[str, Any]] = None,
    level: str = 'INFO'
):
    """
    記錄用戶操作日誌
    
    Args:
        logger: logger 實例
        user: 用戶對象 (支持 Django User 或 SSO User)
        action: 操作描述
        details: 詳細信息
        level: 日誌級別
    """
    username = getattr(user, 'username', str(user))
    user_id = getattr(user, 'id', None)
    
    message = f"用戶 {username} 執行操作: {action}"
    
    extra_data = {
        'action': action,
        'user_id': user_id,
        'username': username,
    }
    if details:
        extra_data.update(details)
    
    log_func = getattr(logger, level.lower(), logger.info)
    log_func(message, extra={'user': username, 'extra_data': extra_data})

