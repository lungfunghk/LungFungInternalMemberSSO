# lungfung_sso/cache.py
"""
緩存管理模組

提供統一的緩存管理功能，用於緩存用戶數據、令牌驗證結果等。
所有緩存鍵均使用統一的前綴和命名規範，以避免衝突並方便管理。
"""
from functools import wraps
import logging

logger = logging.getLogger(__name__)

def _get_settings_value(key, default):
    """安全地獲取 Django 設置值"""
    try:
        from django.conf import settings
        return getattr(settings, key, default)
    except ImportError:
        # Django 未安裝
        return default
    except Exception:
        # Django 設置未配置
        return default

def _get_cache():
    """安全地獲取 Django 緩存"""
    try:
        from django.core.cache import cache
        return cache
    except ImportError:
        # Django 未安裝，返回一個模擬緩存對象
        class MockCache:
            def get(self, key, default=None):
                return default
            def set(self, key, value, timeout=None):
                pass
            def delete(self, key):
                pass
            def clear(self):
                pass
        return MockCache()
    except Exception:
        # Django 設置未配置，返回模擬緩存對象
        class MockCache:
            def get(self, key, default=None):
                return default
            def set(self, key, value, timeout=None):
                pass
            def delete(self, key):
                pass
            def clear(self):
                pass
        return MockCache()

# 從設置中獲取緩存配置
CACHE_KEY_PREFIX = _get_settings_value('CACHE_KEY_PREFIX', 'sso_')

# 從設置中獲取緩存鍵類型
CACHE_TYPE_TOKEN = _get_settings_value('CACHE_TYPE_TOKEN', 'token')
CACHE_TYPE_PERMISSIONS = _get_settings_value('CACHE_TYPE_PERMISSIONS', 'permissions')
CACHE_TYPE_USER = _get_settings_value('CACHE_TYPE_USER', 'user')

# 獲取默認緩存超時設置
TOKEN_CACHE_TTL = _get_settings_value('TOKEN_VERIFICATION_CACHE_TTL', 300)
USER_CACHE_TTL = _get_settings_value('USER_CACHE_TIMEOUT', 300)
PERMISSIONS_CACHE_TTL = _get_settings_value('PERMISSIONS_CACHE_TIMEOUT', USER_CACHE_TTL)

def get_cache_key(key_type, identifier):
    """
    生成標準化的緩存鍵
    
    參數:
        key_type (str): 緩存鍵類型，如 'token', 'permissions', 'user'
        identifier (str): 標識符，如用戶ID、令牌值等
        
    返回:
        str: 標準化的緩存鍵
    """
    return f"{CACHE_KEY_PREFIX}{key_type}_{identifier}"

def get_token_cache_key(token_value):
    """
    生成令牌驗證結果的緩存鍵
    
    參數:
        token_value (str): 令牌值
        
    返回:
        str: 緩存鍵
    """
    return get_cache_key(CACHE_TYPE_TOKEN, token_value)

def get_permissions_cache_key(user_id):
    """
    生成用戶權限數據的緩存鍵
    
    參數:
        user_id (int): 用戶ID
        
    返回:
        str: 緩存鍵
    """
    return get_cache_key(CACHE_TYPE_PERMISSIONS, user_id)

def get_user_cache_key(user_id):
    """
    生成用戶數據的緩存鍵
    
    參數:
        user_id (int): 用戶ID
        
    返回:
        str: 緩存鍵
    """
    return get_cache_key(CACHE_TYPE_USER, user_id)

def cache_user_data(timeout=None):
    """
    裝飾器：緩存用戶數據
    
    將用戶權限和個人資料數據存入緩存，並附加到請求對象。
    
    參數:
        timeout (int, optional): 緩存超時時間（秒）。如果為None，則使用 settings.USER_CACHE_TIMEOUT
        
    使用示例:
        @cache_user_data()
        def my_view(request):
            # 此時 request.user_data 已包含用戶權限和個人資料數據
            return render(request, 'template.html')
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            if not hasattr(request, 'user') or not request.user.is_authenticated:
                logger.debug("用戶未認證，跳過用戶數據緩存")
                return view_func(request, *args, **kwargs)
                
            cache_key = get_user_cache_key(request.user.id)
            user_data = _get_cache().get(cache_key)
            
            if user_data is None:
                logger.debug(f"用戶數據緩存未命中，為用戶ID: {request.user.id} 創建緩存")
                
                # 檢查是否有自定義的用戶權限和個人資料獲取方法
                try:
                    permissions = request.user.get_all_permissions()
                except AttributeError:
                    permissions = None
                    logger.warning(f"用戶對象沒有 get_all_permissions 方法，權限為空")
                
                try:
                    profile = request.user.get_profile()
                except AttributeError:
                    profile = None
                    logger.warning(f"用戶對象沒有 get_profile 方法，個人資料為空")
                
                user_data = {
                    'permissions': permissions,
                    'profile': profile
                }
                
                # 使用配置的超時時間或默認值
                cache_timeout = timeout or USER_CACHE_TTL
                
                _get_cache().set(
                    cache_key, 
                    user_data, 
                    cache_timeout
                )
                logger.debug(f"用戶數據已緩存，過期時間: {cache_timeout}秒")
            else:
                logger.debug(f"使用緩存的用戶數據，用戶ID: {request.user.id}")
                
            request.user_data = user_data
            return view_func(request, *args, **kwargs)
        return wrapped_view
    return decorator

def set_token_verification_cache(token_value, user_obj, timeout=None):
    """
    設置令牌驗證結果緩存
    
    參數:
        token_value (str): 令牌值
        user_obj (User): 用戶對象
        timeout (int, optional): 緩存超時時間（秒）。如果為None，則使用 settings.TOKEN_VERIFICATION_CACHE_TTL
        
    返回:
        bool: 緩存是否設置成功
    """
    cache_key = get_token_cache_key(token_value)
    cache_timeout = timeout or TOKEN_CACHE_TTL
    
    try:
        _get_cache().set(cache_key, user_obj, cache_timeout)
        logger.debug(f"令牌驗證結果已緩存，過期時間: {cache_timeout}秒")
        return True
    except Exception as e:
        logger.error(f"設置令牌驗證緩存失敗: {str(e)}")
        return False

def get_token_verification_cache(token_value):
    """
    獲取令牌驗證結果緩存
    
    參數:
        token_value (str): 令牌值
        
    返回:
        User or None: 用戶對象，如果緩存未命中則返回None
    """
    cache_key = get_token_cache_key(token_value)
    cached_user = _get_cache().get(cache_key)
    
    log_level = getattr(settings, 'SSO_LOGGING_LEVEL', 'DEBUG' if settings.DEBUG else 'INFO')
    if cached_user:
        if log_level == 'DEBUG':
            logger.debug(f"令牌驗證緩存命中，用戶: {cached_user.username}")
    else:
        logger.debug("令牌驗證緩存未命中")
        
    return cached_user

def set_user_permissions_cache(user_id, permissions_data, timeout=None):
    """
    設置用戶權限數據緩存
    
    參數:
        user_id (int): 用戶ID
        permissions_data (dict): 權限數據
        timeout (int, optional): 緩存超時時間（秒）。如果為None，則使用 settings.PERMISSIONS_CACHE_TIMEOUT
        
    返回:
        bool: 緩存是否設置成功
    """
    cache_key = get_permissions_cache_key(user_id)
    cache_timeout = timeout or PERMISSIONS_CACHE_TTL
    
    try:
        _get_cache().set(cache_key, permissions_data, cache_timeout)
        logger.debug(f"用戶權限數據已緩存，用戶ID: {user_id}，過期時間: {cache_timeout}秒")
        return True
    except Exception as e:
        logger.error(f"設置用戶權限緩存失敗: {str(e)}")
        return False

def get_user_permissions_cache(user_id):
    """
    獲取用戶權限數據緩存
    
    參數:
        user_id (int): 用戶ID
        
    返回:
        dict or None: 權限數據，如果緩存未命中則返回None
    """
    cache_key = get_permissions_cache_key(user_id)
    permissions_data = _get_cache().get(cache_key)
    
    log_level = getattr(settings, 'SSO_LOGGING_LEVEL', 'DEBUG' if settings.DEBUG else 'INFO')
    if permissions_data:
        if log_level == 'DEBUG':
            logger.debug(f"用戶權限緩存命中，用戶ID: {user_id}")
    else:
        logger.debug(f"用戶權限緩存未命中，用戶ID: {user_id}")
        
    return permissions_data

def invalidate_user_cache(user_id):
    """
    使用戶相關的所有緩存失效
    
    參數:
        user_id (int): 用戶ID
        
    返回:
        None
    """
    # 刪除用戶數據緩存
    _get_cache().delete(get_user_cache_key(user_id))
    
    # 刪除用戶權限緩存
    _get_cache().delete(get_permissions_cache_key(user_id))
    
    # 注意：無法直接刪除與用戶相關的令牌緩存，因為不知道令牌值
    # 這些緩存將在過期後自動失效
    
    logger.info(f"用戶ID: {user_id} 的緩存已失效")

def invalidate_token_cache(token_value):
    """
    使令牌驗證結果緩存失效
    
    參數:
        token_value (str): 令牌值
        
    返回:
        None
    """
    cache_key = get_token_cache_key(token_value)
    _get_cache().delete(cache_key)
    logger.info(f"令牌緩存已失效")