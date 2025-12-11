"""
LungFung 統一日誌服務

提供完整的日誌管理功能，包括：
- 文件日誌讀取和管理
- 日誌統計
- 請求日誌中間件
- 日誌清理工具

使用方法:
    from lungfung_sso import FileLogService, LoggingMiddleware
    
    # 讀取日誌文件
    service = FileLogService()
    logs = service.read_recent_logs('app.log', lines=100)
    
    # 在 middleware 中使用
    MIDDLEWARE = [
        ...
        'lungfung_sso.logging_service.RequestLoggingMiddleware',
    ]
"""

import logging
import os
import threading
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from functools import wraps


# 線程本地存儲，用於存儲請求上下文
_request_context = threading.local()


def get_request_context() -> Dict[str, Any]:
    """獲取當前請求上下文"""
    return getattr(_request_context, 'data', {})


def set_request_context(**kwargs):
    """設置請求上下文"""
    if not hasattr(_request_context, 'data'):
        _request_context.data = {}
    _request_context.data.update(kwargs)


def clear_request_context():
    """清除請求上下文"""
    if hasattr(_request_context, 'data'):
        _request_context.data = {}


class FileLogService:
    """
    文件日誌服務類
    
    提供日誌文件的讀取、搜索和管理功能。
    """
    
    def __init__(self, log_dir: Optional[Path] = None):
        """
        初始化文件日誌服務
        
        Args:
            log_dir: 日誌目錄路徑，默認從 Django settings 獲取
        """
        if log_dir is None:
            try:
                from django.conf import settings
                log_dir = Path(settings.BASE_DIR) / 'logs'
            except Exception:
                log_dir = Path.cwd() / 'logs'
        
        self.log_dir = Path(log_dir)
    
    def get_log_files(self) -> Dict[str, List[Dict]]:
        """
        獲取可用的日誌文件列表
        
        Returns:
            按類型分組的日誌文件字典
        """
        log_files = {
            'app': [],
            'error': [],
            'celery': [],
            'debug': [],
            'other': [],
        }
        
        if not self.log_dir.exists():
            return log_files
        
        try:
            for log_file in self.log_dir.glob('*.log*'):
                file_info = {
                    'path': str(log_file),
                    'name': log_file.name,
                    'size': log_file.stat().st_size,
                    'size_human': self._format_size(log_file.stat().st_size),
                    'modified': datetime.fromtimestamp(log_file.stat().st_mtime),
                }
                
                # 根據文件名分類
                name_lower = log_file.name.lower()
                if 'error' in name_lower:
                    log_files['error'].append(file_info)
                elif 'app' in name_lower:
                    log_files['app'].append(file_info)
                elif 'celery' in name_lower:
                    log_files['celery'].append(file_info)
                elif 'debug' in name_lower:
                    log_files['debug'].append(file_info)
                else:
                    log_files['other'].append(file_info)
            
            # 按修改時間排序
            for category in log_files:
                log_files[category].sort(key=lambda x: x['modified'], reverse=True)
                
        except Exception as e:
            logging.getLogger(__name__).error(f"Failed to scan log files: {e}")
        
        return log_files
    
    def read_recent_logs(
        self,
        filename: str,
        lines: int = 100,
        level_filter: Optional[str] = None,
        search: Optional[str] = None,
    ) -> List[Dict]:
        """
        讀取日誌文件的最近幾行
        
        Args:
            filename: 日誌文件名
            lines: 讀取行數
            level_filter: 日誌級別過濾
            search: 搜索關鍵字
            
        Returns:
            解析後的日誌記錄列表
        """
        logs = []
        file_path = self.log_dir / filename
        
        # 安全檢查
        try:
            file_path = file_path.resolve()
            if not str(file_path).startswith(str(self.log_dir.resolve())):
                raise ValueError("Invalid file path")
        except Exception:
            return logs
        
        if not file_path.exists():
            return logs
        
        try:
            # 讀取文件末尾
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                all_lines = f.readlines()
                recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
            
            # 解析日誌行
            for line in recent_lines:
                line = line.strip()
                if not line:
                    continue
                
                log_entry = self._parse_log_line(line)
                
                # 應用過濾器
                if level_filter and log_entry.get('level', '').upper() != level_filter.upper():
                    continue
                
                if search and search.lower() not in log_entry.get('message', '').lower():
                    continue
                
                logs.append(log_entry)
                
        except Exception as e:
            logging.getLogger(__name__).error(f"Failed to read log file {filename}: {e}")
        
        return logs
    
    def _parse_log_line(self, line: str) -> Dict:
        """解析日誌行"""
        try:
            # 嘗試解析標準格式: [LEVEL] TIMESTAMP [logger:line] message
            # 或者: LEVEL TIMESTAMP logger message
            
            if line.startswith('['):
                # 格式: [LEVEL] TIMESTAMP [logger:line] message
                parts = line.split(']', 2)
                if len(parts) >= 3:
                    level = parts[0].strip('[')
                    rest = parts[1].strip() + parts[2]
                    timestamp_end = rest.find('[')
                    if timestamp_end > 0:
                        timestamp = rest[:timestamp_end].strip()
                        rest = rest[timestamp_end:]
                        logger_end = rest.find(']')
                        if logger_end > 0:
                            logger = rest[1:logger_end]
                            message = rest[logger_end+1:].strip()
                            return {
                                'level': level,
                                'timestamp': timestamp,
                                'logger': logger,
                                'message': message,
                                'raw': line
                            }
            
            # 嘗試解析簡單格式: LEVEL TIMESTAMP logger message
            parts = line.split(' ', 3)
            if len(parts) >= 4:
                return {
                    'level': parts[0],
                    'timestamp': f"{parts[1]} {parts[2]}",
                    'logger': parts[3].split(' ')[0] if ' ' in parts[3] else '',
                    'message': parts[3],
                    'raw': line
                }
            
        except Exception:
            pass
        
        # 無法解析，返回原始行
        return {
            'level': 'UNKNOWN',
            'timestamp': '',
            'logger': '',
            'message': line,
            'raw': line
        }
    
    def _format_size(self, size: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
    
    def get_log_statistics(self) -> Dict[str, Any]:
        """
        獲取日誌統計信息
        
        Returns:
            統計信息字典
        """
        stats = {
            'total_files': 0,
            'total_size': 0,
            'total_size_human': '0 B',
            'by_category': {},
        }
        
        log_files = self.get_log_files()
        
        for category, files in log_files.items():
            category_size = sum(f['size'] for f in files)
            stats['by_category'][category] = {
                'count': len(files),
                'size': category_size,
                'size_human': self._format_size(category_size),
            }
            stats['total_files'] += len(files)
            stats['total_size'] += category_size
        
        stats['total_size_human'] = self._format_size(stats['total_size'])
        
        return stats
    
    def cleanup_old_logs(self, days: int = 30, dry_run: bool = True) -> List[str]:
        """
        清理超過指定天數的日誌文件
        
        Args:
            days: 保留天數
            dry_run: 是否只是預覽，不實際刪除
            
        Returns:
            被刪除(或將被刪除)的文件列表
        """
        deleted = []
        cutoff = datetime.now() - timedelta(days=days)
        
        if not self.log_dir.exists():
            return deleted
        
        for log_file in self.log_dir.glob('*.log*'):
            try:
                mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                if mtime < cutoff:
                    if not dry_run:
                        log_file.unlink()
                    deleted.append(str(log_file))
            except Exception as e:
                logging.getLogger(__name__).error(f"Error processing {log_file}: {e}")
        
        return deleted


class RequestLoggingMiddleware:
    """
    請求日誌中間件
    
    自動記錄每個 HTTP 請求的基本信息。
    
    在 settings.py 中添加:
        MIDDLEWARE = [
            ...
            'lungfung_sso.logging_service.RequestLoggingMiddleware',
        ]
    """
    
    def __init__(self, get_response: Callable):
        self.get_response = get_response
        self.logger = logging.getLogger('apps.requests')
        
        # 不記錄的路徑前綴
        self.exclude_paths = [
            '/static/',
            '/media/',
            '/favicon.ico',
            '/health/',
            '/__debug__/',
        ]
        
        # 不記錄的路徑後綴
        self.exclude_suffixes = [
            '.js', '.css', '.png', '.jpg', '.jpeg', '.gif', '.ico', '.svg', '.woff', '.woff2'
        ]
    
    def __call__(self, request):
        # 檢查是否應該跳過
        if self._should_skip(request.path):
            return self.get_response(request)
        
        # 生成請求 ID
        import uuid
        request_id = str(uuid.uuid4())[:8]
        
        # 設置請求上下文
        set_request_context(
            request_id=request_id,
            user=self._get_username(request),
            ip=self._get_client_ip(request),
            path=request.path,
            method=request.method,
        )
        
        # 記錄請求開始
        start_time = datetime.now()
        
        # 處理請求
        response = self.get_response(request)
        
        # 計算處理時間
        duration = (datetime.now() - start_time).total_seconds() * 1000
        
        # 記錄請求完成
        self._log_request(request, response, duration, request_id)
        
        # 清除請求上下文
        clear_request_context()
        
        return response
    
    def _should_skip(self, path: str) -> bool:
        """檢查是否應該跳過記錄"""
        for prefix in self.exclude_paths:
            if path.startswith(prefix):
                return True
        
        for suffix in self.exclude_suffixes:
            if path.endswith(suffix):
                return True
        
        return False
    
    def _get_username(self, request) -> str:
        """獲取用戶名"""
        if hasattr(request, 'user'):
            user = request.user
            if hasattr(user, 'is_authenticated') and user.is_authenticated:
                return getattr(user, 'username', str(user))
        return 'anonymous'
    
    def _get_client_ip(self, request) -> str:
        """獲取客戶端 IP"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '')
    
    def _log_request(self, request, response, duration: float, request_id: str):
        """記錄請求日誌"""
        status_code = response.status_code
        
        # 根據狀態碼選擇日誌級別
        if status_code >= 500:
            log_func = self.logger.error
        elif status_code >= 400:
            log_func = self.logger.warning
        else:
            log_func = self.logger.info
        
        message = (
            f"[{request_id}] {request.method} {request.path} "
            f"-> {status_code} ({duration:.1f}ms) "
            f"user={self._get_username(request)} ip={self._get_client_ip(request)}"
        )
        
        log_func(message)


def log_function_call(
    logger_name: str = 'apps',
    log_args: bool = True,
    log_result: bool = False,
    log_exceptions: bool = True,
):
    """
    函數調用日誌裝飾器
    
    自動記錄函數調用、參數和返回值。
    
    Args:
        logger_name: logger 名稱
        log_args: 是否記錄參數
        log_result: 是否記錄返回值
        log_exceptions: 是否記錄異常
        
    Example:
        @log_function_call('apps.services')
        def process_approval(approval_id, action):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = logging.getLogger(logger_name)
            func_name = f"{func.__module__}.{func.__name__}"
            
            # 記錄調用
            if log_args:
                # 過濾敏感參數
                safe_kwargs = {
                    k: v for k, v in kwargs.items()
                    if k not in ('password', 'token', 'secret', 'key')
                }
                logger.debug(f"Calling {func_name} with kwargs={safe_kwargs}")
            else:
                logger.debug(f"Calling {func_name}")
            
            try:
                result = func(*args, **kwargs)
                
                if log_result:
                    logger.debug(f"{func_name} returned: {type(result).__name__}")
                
                return result
                
            except Exception as e:
                if log_exceptions:
                    logger.exception(f"{func_name} raised {type(e).__name__}: {e}")
                raise
        
        return wrapper
    return decorator


class ContextLogger:
    """
    上下文感知的日誌記錄器
    
    自動從請求上下文中獲取用戶和請求 ID 信息。
    
    Example:
        logger = ContextLogger('apps.approvals')
        logger.info('Approval created', approval_id=123)  # 自動包含用戶和請求ID
    """
    
    def __init__(self, name: str, system: Optional[str] = None):
        self._logger = logging.getLogger(name)
        self._system = system
    
    def _get_context_info(self) -> Dict[str, str]:
        """獲取上下文信息"""
        ctx = get_request_context()
        return {
            'user': ctx.get('user', 'system'),
            'request_id': ctx.get('request_id', '-'),
            'ip': ctx.get('ip', '-'),
        }
    
    def _format_message(self, message: str, **kwargs) -> str:
        """格式化消息"""
        ctx = self._get_context_info()
        prefix = f"[{ctx['request_id']}] [{ctx['user']}]"
        
        if kwargs:
            details = ' '.join(f"{k}={v}" for k, v in kwargs.items())
            return f"{prefix} {message} | {details}"
        return f"{prefix} {message}"
    
    def debug(self, message: str, **kwargs):
        self._logger.debug(self._format_message(message, **kwargs))
    
    def info(self, message: str, **kwargs):
        self._logger.info(self._format_message(message, **kwargs))
    
    def warning(self, message: str, **kwargs):
        self._logger.warning(self._format_message(message, **kwargs))
    
    def error(self, message: str, **kwargs):
        self._logger.error(self._format_message(message, **kwargs))
    
    def exception(self, message: str, **kwargs):
        self._logger.exception(self._format_message(message, **kwargs))

