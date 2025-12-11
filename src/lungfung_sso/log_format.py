"""
LungFung 統一日誌格式化工具

提供標準化的日誌消息格式，確保所有子系統的日誌格式一致。

使用方法:
    from lungfung_sso import LogFormatter, StructuredLogger
    
    # 方法1: 使用 LogFormatter 生成結構化日誌字典
    log_data = LogFormatter.info(
        user='admin',
        action='create_approval',
        details={'approval_id': 123}
    )
    logger.info(json.dumps(log_data))
    
    # 方法2: 使用 StructuredLogger 直接記錄
    slogger = StructuredLogger('apps.approvals')
    slogger.info('create_approval', user='admin', approval_id=123)
"""

import json
import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime


class LogFormatter:
    """
    統一的日誌格式化工具類
    用於生成標準化的日誌消息字典
    """
    
    @staticmethod
    def format_log(
        level: str,
        user: str,
        action: str,
        details: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        request_id: Optional[str] = None,
        system: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        生成標準格式的日誌字典
        
        Args:
            level: 日誌級別 (INFO/ERROR/WARNING/DEBUG)
            user: 用戶名稱
            action: 執行的操作
            details: 詳細信息字典 (用於INFO級別)
            error: 錯誤信息 (用於ERROR級別)
            request_id: 請求ID (用於追蹤)
            system: 系統代碼
            
        Returns:
            包含完整日誌信息的字典
        """
        try:
            from django.utils import timezone
            timestamp = timezone.now().isoformat()
        except ImportError:
            timestamp = datetime.utcnow().isoformat() + 'Z'
        
        log_dict = {
            "timestamp": timestamp,
            "level": level,
            "user": user,
            "action": action
        }
        
        if system is not None:
            log_dict["system"] = system
            
        if request_id is not None:
            log_dict["request_id"] = request_id
        
        if details is not None:
            log_dict["details"] = details
            
        if error is not None:
            log_dict["error"] = error
            
        return log_dict
    
    @classmethod
    def info(
        cls,
        user: str,
        action: str,
        details: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        生成 INFO 級別的日誌
        
        Args:
            user: 用戶名稱
            action: 執行的操作
            details: 詳細信息字典
            **kwargs: 其他參數 (request_id, system 等)
            
        Returns:
            INFO級別的日誌字典
        """
        return cls.format_log(
            level="INFO",
            user=user,
            action=action,
            details=details,
            **kwargs
        )
    
    @classmethod
    def error(
        cls,
        user: str,
        action: str,
        error: str,
        details: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        生成 ERROR 級別的日誌
        
        Args:
            user: 用戶名稱
            action: 執行的操作
            error: 錯誤信息
            details: 額外的詳細信息字典 (可選)
            **kwargs: 其他參數 (request_id, system 等)
            
        Returns:
            ERROR級別的日誌字典
        """
        return cls.format_log(
            level="ERROR",
            user=user,
            action=action,
            details=details,
            error=error,
            **kwargs
        )
    
    @classmethod
    def warning(
        cls,
        user: str,
        action: str,
        details: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        生成 WARNING 級別的日誌
        
        Args:
            user: 用戶名稱
            action: 執行的操作
            details: 詳細信息字典
            **kwargs: 其他參數 (request_id, system 等)
            
        Returns:
            WARNING級別的日誌字典
        """
        return cls.format_log(
            level="WARNING",
            user=user,
            action=action,
            details=details,
            **kwargs
        )
    
    @classmethod
    def debug(
        cls,
        user: str,
        action: str,
        details: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        生成 DEBUG 級別的日誌
        
        Args:
            user: 用戶名稱
            action: 執行的操作
            details: 詳細信息字典
            **kwargs: 其他參數 (request_id, system 等)
            
        Returns:
            DEBUG級別的日誌字典
        """
        return cls.format_log(
            level="DEBUG",
            user=user,
            action=action,
            details=details,
            **kwargs
        )
    
    @classmethod
    def audit(
        cls,
        user: str,
        action: str,
        resource_type: str,
        resource_id: Any,
        old_value: Optional[Any] = None,
        new_value: Optional[Any] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        生成審計日誌
        
        Args:
            user: 用戶名稱
            action: 操作類型 (create/update/delete/view)
            resource_type: 資源類型 (如 'ApprovalRequest')
            resource_id: 資源ID
            old_value: 修改前的值 (用於 update)
            new_value: 修改後的值 (用於 create/update)
            **kwargs: 其他參數
            
        Returns:
            審計日誌字典
        """
        details = {
            "resource_type": resource_type,
            "resource_id": str(resource_id),
            "operation": action,
        }
        
        if old_value is not None:
            details["old_value"] = old_value
        if new_value is not None:
            details["new_value"] = new_value
        
        return cls.format_log(
            level="INFO",
            user=user,
            action=f"audit_{action}",
            details=details,
            **kwargs
        )


class StructuredLogger:
    """
    結構化日誌記錄器
    
    提供更便捷的日誌記錄方法，自動處理結構化數據。
    
    Example:
        logger = StructuredLogger('apps.approvals')
        logger.info('approval_created', user='admin', approval_id=123)
        logger.error('approval_failed', user='admin', error='Invalid data')
    """
    
    def __init__(
        self,
        name: str,
        system: Optional[str] = None,
        default_user: str = 'system'
    ):
        """
        初始化結構化日誌記錄器
        
        Args:
            name: logger 名稱
            system: 系統代碼
            default_user: 默認用戶名
        """
        self._logger = logging.getLogger(name)
        self._system = system
        self._default_user = default_user
    
    def _log(
        self,
        level: str,
        action: str,
        user: Optional[str] = None,
        error: Optional[str] = None,
        **kwargs
    ):
        """內部日誌記錄方法"""
        log_func = getattr(self._logger, level.lower(), self._logger.info)
        
        # 構建結構化數據
        log_data = LogFormatter.format_log(
            level=level.upper(),
            user=user or self._default_user,
            action=action,
            details=kwargs if kwargs else None,
            error=error,
            system=self._system,
        )
        
        # 構建消息
        message = f"[{action}] user={log_data['user']}"
        if error:
            message += f" error={error}"
        if kwargs:
            # 只顯示關鍵字段
            key_fields = ['id', 'approval_id', 'workflow_id', 'status', 'result']
            shown_fields = {k: v for k, v in kwargs.items() if k in key_fields}
            if shown_fields:
                message += f" {shown_fields}"
        
        # 記錄日誌
        log_func(message, extra={'extra_data': log_data})
    
    def debug(self, action: str, user: Optional[str] = None, **kwargs):
        """記錄 DEBUG 級別日誌"""
        self._log('DEBUG', action, user, **kwargs)
    
    def info(self, action: str, user: Optional[str] = None, **kwargs):
        """記錄 INFO 級別日誌"""
        self._log('INFO', action, user, **kwargs)
    
    def warning(self, action: str, user: Optional[str] = None, **kwargs):
        """記錄 WARNING 級別日誌"""
        self._log('WARNING', action, user, **kwargs)
    
    def error(self, action: str, user: Optional[str] = None, error: Optional[str] = None, **kwargs):
        """記錄 ERROR 級別日誌"""
        self._log('ERROR', action, user, error=error, **kwargs)
    
    def exception(self, action: str, exc: Exception, user: Optional[str] = None, **kwargs):
        """記錄異常日誌"""
        self._logger.exception(
            f"[{action}] user={user or self._default_user} error={exc}",
            extra={'extra_data': {
                'action': action,
                'user': user or self._default_user,
                'exception_type': type(exc).__name__,
                **kwargs
            }}
        )
    
    def audit(
        self,
        action: str,
        resource_type: str,
        resource_id: Any,
        user: Optional[str] = None,
        old_value: Optional[Any] = None,
        new_value: Optional[Any] = None,
        **kwargs
    ):
        """記錄審計日誌"""
        log_data = LogFormatter.audit(
            user=user or self._default_user,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            old_value=old_value,
            new_value=new_value,
            system=self._system,
        )
        
        message = f"[AUDIT] {action} {resource_type}#{resource_id} by {log_data['user']}"
        self._logger.info(message, extra={'extra_data': log_data})


def create_logger(
    name: str,
    system: Optional[str] = None
) -> StructuredLogger:
    """
    創建結構化日誌記錄器的便捷函數
    
    Args:
        name: logger 名稱
        system: 系統代碼
        
    Returns:
        StructuredLogger 實例
        
    Example:
        logger = create_logger('apps.approvals', system='APS')
        logger.info('approval_created', user='admin', approval_id=123)
    """
    return StructuredLogger(name, system=system)
