"""
LungFung SSO Authentication Module

A Django package providing SSO authentication functionality
for LungFung projects.

Features:
- SSO 認證和授權
- 統一的日誌配置和服務
- 權限檢查和管理
"""

__version__ = "1.1.2"
__author__ = "LungFung IT Team"

# 主要組件導入
# 先導入不依賴 Django 的組件
from .settings_helper import (
    configure_sso_settings,
    add_sso_middleware,
    add_sso_app,
)

# 日誌配置 (不依賴 Django 運行時)
from .logging_config import (
    configure_logging,
    get_logger,
    log_exception,
    log_user_action,
    ColoredFormatter,
    JSONFormatter,
)

# 日誌格式化工具 (不依賴 Django 運行時)
from .log_format import (
    LogFormatter,
    StructuredLogger,
    create_logger,
)

# 使用延遲導入模式來處理 Django 依賴組件
def __getattr__(name):
    """延遲導入屬性，只有在實際使用時才導入 Django 依賴組件"""
    
    # Django 依賴組件的映射
    django_components = {
        'SSOAuthentication': ('authentication', 'SSOAuthentication'),
        'JWTAuthenticationMiddleware': ('middleware', 'JWTAuthenticationMiddleware'),
        'ModulePermissionRequiredMixin': ('permissions', 'ModulePermissionRequiredMixin'),
        'SSOPermission': ('permissions', 'SSOPermission'),
        'SSOperationPermission': ('permissions', 'SSOperationPermission'),
        'check_permission': ('permissions', 'check_permission'),
        'module_permission_required': ('permissions', 'module_permission_required'),
        'User': ('models', 'User'),
        'UserAdapter': ('user_adapter', 'UserAdapter'),
        'cache_user_data': ('cache', 'cache_user_data'),
        'invalidate_user_cache': ('cache', 'invalidate_user_cache'),
        'get_token_verification_cache': ('cache', 'get_token_verification_cache'),
        'set_token_verification_cache': ('cache', 'set_token_verification_cache'),
        'get_user_permissions_cache': ('cache', 'get_user_permissions_cache'),
        'set_user_permissions_cache': ('cache', 'set_user_permissions_cache'),
        'invalidate_token_cache': ('cache', 'invalidate_token_cache'),
        # 日誌服務組件 (需要 Django)
        'FileLogService': ('logging_service', 'FileLogService'),
        'RequestLoggingMiddleware': ('logging_service', 'RequestLoggingMiddleware'),
        'ContextLogger': ('logging_service', 'ContextLogger'),
        'log_function_call': ('logging_service', 'log_function_call'),
        'get_request_context': ('logging_service', 'get_request_context'),
        'set_request_context': ('logging_service', 'set_request_context'),
    }
    
    # 異常組件（通常不依賴 Django）
    exception_components = {
        'SSOException': ('exceptions', 'SSOException'),
        'SSOAuthenticationError': ('exceptions', 'SSOAuthenticationError'),
        'SSOPermissionError': ('exceptions', 'SSOPermissionError'),
        'SSOServiceError': ('exceptions', 'SSOServiceError'),
        'TokenError': ('exceptions', 'TokenError'),
        'TokenExpiredError': ('exceptions', 'TokenExpiredError'),
        'PermissionDeniedError': ('exceptions', 'PermissionDeniedError'),
    }
    
    # 嘗試導入異常組件
    if name in exception_components:
        try:
            module_name, attr_name = exception_components[name]
            module = __import__(f'lungfung_sso.{module_name}', fromlist=[attr_name])
            component = getattr(module, attr_name)
            globals()[name] = component
            return component
        except Exception:
            pass
    
    # 嘗試導入 Django 依賴組件
    if name in django_components:
        try:
            module_name, attr_name = django_components[name]
            module = __import__(f'lungfung_sso.{module_name}', fromlist=[attr_name])
            component = getattr(module, attr_name)
            globals()[name] = component
            return component
        except Exception as e:
            import warnings
            warnings.warn(f"Failed to import {name}: {e}. Make sure Django is properly configured.")
            raise AttributeError(f"module '{__name__}' has no attribute '{name}'. "
                               f"This component requires Django to be configured. Error: {e}")
    
    # 如果找不到屬性，拋出標準錯誤
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

# 便捷導入
__all__ = [
    # 版本信息
    '__version__',
    '__author__',
    
    # 核心服務
    'SSOAuthentication',
    
    # 中間件
    'JWTAuthenticationMiddleware',
    'RequestLoggingMiddleware',
    
    # 權限相關
    'ModulePermissionRequiredMixin',
    'SSOPermission', 
    'SSOperationPermission',
    'check_permission',
    'module_permission_required',
    
    # 模型
    'User',
    
    # 用戶適配器
    'UserAdapter',
    
    # 異常類
    'SSOException',
    'SSOAuthenticationError',
    'SSOPermissionError',
    'SSOServiceError',
    'TokenError',
    'TokenExpiredError',
    'PermissionDeniedError',
    
    # 緩存功能
    'cache_user_data',
    'invalidate_user_cache',
    'get_token_verification_cache',
    'set_token_verification_cache',
    'get_user_permissions_cache',
    'set_user_permissions_cache',
    'invalidate_token_cache',
    
    # 設置助手
    'configure_sso_settings',
    'add_sso_middleware',
    'add_sso_app',
    
    # 日誌配置
    'configure_logging',
    'get_logger',
    'log_exception',
    'log_user_action',
    'ColoredFormatter',
    'JSONFormatter',
    
    # 日誌格式化
    'LogFormatter',
    'StructuredLogger',
    'create_logger',
    
    # 日誌服務
    'FileLogService',
    'ContextLogger',
    'log_function_call',
    'get_request_context',
    'set_request_context',
]

# 包級別配置
default_app_config = 'lungfung_sso.apps.LungfungSsoConfig'