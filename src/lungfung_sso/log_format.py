from django.utils import timezone
from typing import Any, Dict, Optional

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
        error: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        生成標準格式的日誌字典
        
        Args:
            level: 日誌級別 (INFO/ERROR/WARNING/DEBUG)
            user: 用戶名稱
            action: 執行的操作
            details: 詳細信息字典 (用於INFO級別)
            error: 錯誤信息 (用於ERROR級別)
            
        Returns:
            包含完整日誌信息的字典
        """
        log_dict = {
            "timestamp": timezone.now().isoformat(),
            "level": level,
            "user": user,
            "action": action
        }
        
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
        details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        生成 INFO 級別的日誌
        
        Args:
            user: 用戶名稱
            action: 執行的操作
            details: 詳細信息字典
            
        Returns:
            INFO級別的日誌字典
        """
        return cls.format_log(
            level="INFO",
            user=user,
            action=action,
            details=details
        )
    
    @classmethod
    def error(
        cls,
        user: str,
        action: str,
        error: str,
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        生成 ERROR 級別的日誌
        
        Args:
            user: 用戶名稱
            action: 執行的操作
            error: 錯誤信息
            details: 額外的詳細信息字典 (可選)
            
        Returns:
            ERROR級別的日誌字典
        """
        return cls.format_log(
            level="ERROR",
            user=user,
            action=action,
            details=details,
            error=error
        )
    
    @classmethod
    def warning(
        cls,
        user: str,
        action: str,
        details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        生成 WARNING 級別的日誌
        
        Args:
            user: 用戶名稱
            action: 執行的操作
            details: 詳細信息字典
            
        Returns:
            WARNING級別的日誌字典
        """
        return cls.format_log(
            level="WARNING",
            user=user,
            action=action,
            details=details
        )
    
    @classmethod
    def debug(
        cls,
        user: str,
        action: str,
        details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        生成 DEBUG 級別的日誌
        
        Args:
            user: 用戶名稱
            action: 執行的操作
            details: 詳細信息字典
            
        Returns:
            DEBUG級別的日誌字典
        """
        return cls.format_log(
            level="DEBUG",
            user=user,
            action=action,
            details=details
        ) 