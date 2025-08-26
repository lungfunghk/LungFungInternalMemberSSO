# apps/core/exceptions.py
from django.conf import settings

class SSOAuthenticationError(Exception):
    def __init__(self, message, code=None):
        self.message = message
        self.code = code or 'authentication_error'
        super().__init__(message)

class TokenError(SSOAuthenticationError):
    def __init__(self, message=None, code=None):
        # 從設置中獲取錯誤訊息
        error_config = getattr(settings, 'ERROR_RESPONSE', {}).get('TOKEN_INVALID', {})
        default_message = error_config.get('message', 'Invalid authentication token')
        default_code = error_config.get('code', 'token_invalid')
        
        super().__init__(
            message=message or default_message, 
            code=code or default_code
        )

class TokenExpiredError(TokenError):
    def __init__(self, message=None, code=None):
        # 從設置中獲取錯誤訊息
        error_config = getattr(settings, 'ERROR_RESPONSE', {}).get('TOKEN_EXPIRED', {})
        default_message = error_config.get('message', 'Authentication token expired')
        default_code = error_config.get('code', 'token_expired')
        
        super().__init__(
            message=message or default_message, 
            code=code or default_code
        )

class PermissionDeniedError(SSOAuthenticationError):
    def __init__(self, message=None, code=None):
        # 從設置中獲取錯誤訊息
        error_config = getattr(settings, 'ERROR_RESPONSE', {}).get('PERMISSION_DENIED', {})
        default_message = error_config.get('message', 'Permission denied')
        default_code = error_config.get('code', 'permission_denied')
        
        super().__init__(
            message=message or default_message, 
            code=code or default_code
        )

class SSORateLimitError(SSOAuthenticationError):
    def __init__(self, message=None, code=None):
        # 從設置中獲取錯誤訊息
        error_config = getattr(settings, 'ERROR_RESPONSE', {}).get('RATE_LIMIT', {})
        default_message = error_config.get('message', 'Too many requests to authentication service')
        default_code = error_config.get('code', 'rate_limit')
        
        super().__init__(
            message=message or default_message, 
            code=code or default_code
        )

class SSOServiceUnavailableError(SSOAuthenticationError):
    def __init__(self, message=None, code=None):
        # 從設置中獲取錯誤訊息
        error_config = getattr(settings, 'ERROR_RESPONSE', {}).get('SERVICE_UNAVAILABLE', {})
        default_message = error_config.get('message', 'Authentication service is temporarily unavailable')
        default_code = error_config.get('code', 'service_unavailable')
        
        super().__init__(
            message=message or default_message, 
            code=code or default_code
        )