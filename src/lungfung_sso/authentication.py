# apps/core/authentication.py
from django.conf import settings
from django.core.cache import cache
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
import requests
import json
import logging
from .exceptions import TokenError, TokenExpiredError
from .models import User
from .cache import get_token_verification_cache, set_token_verification_cache, get_user_permissions_cache, set_user_permissions_cache

logger = logging.getLogger(__name__)

class SSOAuthentication(BaseAuthentication):
    """
    單點登錄認證後端
    
    使用 SSO 服務進行基於 JWT 的身份驗證。
    支持從 Authorization 頭或 Cookie 中獲取 token。
    包含緩存機制以減少對 SSO 服務的請求。
    """
    
    def authenticate(self, request):
        """
        從請求中提取和驗證認證令牌
        
        參數:
            request: HTTP 請求對象
            
        返回:
            (user, None) 或 None
        
        可能引發的異常:
            AuthenticationFailed: 認證失敗時
            TokenError: 令牌無效時
            TokenExpiredError: 令牌已過期時
        """
        # 從 HTTP 頭或 cookie 中獲取令牌
        try:
            token = self._get_token_from_request(request)
            if not token:
                logger.debug("未找到令牌，跳過 SSO 認證")
                return None
                
            # 從令牌獲取用戶
            user = self._get_user_from_token(token)
            if not user:
                logger.warning("令牌驗證失敗，無法獲取用戶")
                raise TokenError("無效的認證令牌")
                
            # 獲取用戶權限
            self._load_user_permissions(user)
            
            return (user, None)
        except TokenError as e:
            logger.warning(f"令牌錯誤: {str(e)}")
            raise AuthenticationFailed(str(e))
        except TokenExpiredError as e:
            logger.warning(f"令牌已過期: {str(e)}")
            raise AuthenticationFailed(str(e))
        except Exception as e:
            logger.error(f"認證過程發生意外錯誤: {str(e)}", exc_info=True)
            raise AuthenticationFailed("認證過程發生錯誤")
            
    def _get_token_from_request(self, request):
        """
        從請求中提取認證令牌
        
        按以下順序檢查:
        1. Authorization 頭 (Bearer token)
        2. auth_access_token cookie
        
        參數:
            request: HTTP 請求對象
            
        返回:
            str 或 None: 令牌值或 None（如果未找到）
        """
        # 檢查 Authorization 頭
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Bearer '):
            logger.debug("從 Authorization 頭獲取令牌")
            return auth_header[7:].strip()
            
        # 檢查 cookie
        token = request.COOKIES.get('auth_access_token')
        if token:
            logger.debug("從 cookie 獲取令牌")
            return token
            
        logger.debug("未找到令牌")
        return None
        
    def _get_user_from_token(self, token):
        """
        驗證令牌並獲取用戶信息
        
        首先檢查緩存，如果未命中則向 SSO 服務發送驗證請求。
        成功時將用戶信息存入緩存以加速後續請求。
        
        參數:
            token: 認證令牌
            
        返回:
            User 或 None: 用戶對象或 None（如果驗證失敗）
            
        可能引發的異常:
            TokenError: 令牌無效時
            TokenExpiredError: 令牌已過期時
        """
        # 檢查緩存
        cached_user = get_token_verification_cache(token)
        if cached_user:
            logger.debug(f"使用緩存的令牌驗證結果，用戶: {cached_user.username}")
            return cached_user
            
        # 驗證令牌
        try:
            logger.debug(f"驗證令牌: {token[:10]}...")
            verify_response = requests.post(
                f"{settings.SSO_SERVICE['URL']}{settings.SSO_SERVICE['TOKEN_VERIFY_URL']}",
                json={'token': token},
                verify=settings.SSO_SERVICE['VERIFY_SSL'],
                timeout=5
            )
            
            logger.debug(f"SSO 響應狀態: {verify_response.status_code}")
            
            if verify_response.status_code == 200:
                user_data = verify_response.json()
                logger.info(f"令牌驗證成功，用戶: {user_data.get('username', 'unknown')}")
                
                # 建立用戶對象
                user = User(user_data)
                
                # 緩存驗證結果
                set_token_verification_cache(token, user)
                
                return user
            elif verify_response.status_code == 401:
                error_data = verify_response.json()
                logger.warning(f"令牌已過期: {json.dumps(error_data)}")
                
                if error_data.get('code') == 'token_expired':
                    raise TokenExpiredError("認證令牌已過期")
                else:
                    raise TokenError("無效的認證令牌")
            else:
                logger.error(f"令牌驗證失敗: HTTP {verify_response.status_code}, 響應: {verify_response.text}")
                raise TokenError(f"令牌驗證失敗: {verify_response.text}")
                
        except requests.RequestException as e:
            logger.error(f"SSO 服務連接錯誤: {str(e)}")
            raise TokenError(f"無法連接 SSO 服務: {str(e)}")
            
    def _load_user_permissions(self, user):
        """
        加載用戶權限
        
        首先檢查緩存，如果未命中則向 SSO 服務請求用戶權限數據。
        成功時將權限數據存入緩存以加速後續請求。
        
        參數:
            user: 用戶對象
            
        返回:
            None
        """
        if not hasattr(user, 'id') or not user.id:
            logger.warning("用戶對象缺少 id 屬性，無法加載權限")
            return
            
        # 檢查緩存
        permissions_data = get_user_permissions_cache(user.id)
        
        if permissions_data:
            logger.debug(f"使用緩存的用戶權限數據，用戶ID: {user.id}")
            user.set_permissions(permissions_data)
            return
            
        # 從 SSO 服務獲取權限
        try:
            logger.debug(f"從 SSO 服務獲取用戶權限，用戶ID: {user.id}")
            permissions_response = requests.get(
                f"{settings.SSO_SERVICE['URL']}{settings.SSO_SERVICE['USER_PERMISSIONS_URL']}",
                params={'user_id': user.id},
                headers={'Authorization': f'Bearer {user.token}'},
                verify=settings.SSO_SERVICE['VERIFY_SSL'],
                timeout=5
            )
            
            if permissions_response.status_code == 200:
                permissions_data = permissions_response.json()
                logger.info(f"成功獲取用戶權限，用戶ID: {user.id}")
                
                # 設置用戶權限
                user.set_permissions(permissions_data)
                
                # 緩存權限數據
                set_user_permissions_cache(user.id, permissions_data)
            else:
                logger.error(f"獲取用戶權限失敗: HTTP {permissions_response.status_code}, 響應: {permissions_response.text}")
        except requests.RequestException as e:
            logger.error(f"獲取用戶權限時發生錯誤: {str(e)}")
        except Exception as e:
            logger.error(f"處理用戶權限時發生意外錯誤: {str(e)}", exc_info=True)