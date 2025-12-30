# apps/core/middleware.py
from django.http import JsonResponse, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.conf import settings
from django.core.cache import cache
from django.contrib.auth.models import AnonymousUser
from django.contrib import messages
from .exceptions import TokenError, TokenExpiredError, PermissionDeniedError
from .models import User  # 導入統一的 User 類
from .cache import get_token_verification_cache, set_token_verification_cache

import requests
import time
import logging
from urllib.parse import quote

logger = logging.getLogger(__name__)

# 嘗試導入 prometheus_client，如果不可用則使用模擬對象
try:
    from prometheus_client import Counter, Histogram
    
    # 添加監控指標
    auth_requests = Counter(
        'simple_docking_auth_requests_total',
        'Total auth requests',
        ['status']
    )
    
    auth_latency = Histogram(
        'simple_docking_auth_latency_seconds',
        'Auth request latency'
    )
    
    PROMETHEUS_AVAILABLE = True
except ImportError:
    # 創建模擬的監控對象
    class MockMetric:
        def inc(self, *args, **kwargs):
            pass
        
        def labels(self, *args, **kwargs):
            return self
        
        def observe(self, *args, **kwargs):
            pass
        
        def time(self):
            return MockContextManager()
    
    class MockContextManager:
        def __enter__(self):
            return self
        
        def __exit__(self, *args):
            pass
    
    auth_requests = MockMetric()
    auth_latency = MockMetric()
    
    PROMETHEUS_AVAILABLE = False
    logger.warning("prometheus_client not available, monitoring metrics disabled")

# 創建SSO服務的請求會話
sso_session = None

def get_sso_session():
    """獲取或創建SSO服務的請求會話"""
    global sso_session
    if sso_session is None:
        # 創建會話並配置連接池
        pool_connections = getattr(settings, 'SSO_CONNECTION_POOL_SIZE', 20)
        pool_maxsize = getattr(settings, 'SSO_CONNECTION_POOL_SIZE', 20)
        max_retries = getattr(settings, 'SSO_MAX_RETRIES', 0)
        
        sso_session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=pool_connections,
            pool_maxsize=pool_maxsize,
            max_retries=max_retries
        )
        # 為所有URLs配置連接池適配器
        sso_session.mount('http://', adapter)
        sso_session.mount('https://', adapter)
        
        logger.info(f"已創建SSO服務的請求會話：連接池大小={pool_maxsize}，最大重試次數={max_retries}")
    
    return sso_session

class JWTAuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # 初始化時獲取SSO會話，只需創建一次
        self.sso_session = get_sso_session()
        
    def __call__(self, request):
        start_time = time.time()
        
        # 獲取日誌級別
        log_level = getattr(settings, 'SSO_LOGGING_LEVEL', 'DEBUG' if settings.DEBUG else 'INFO')
        detailed_logging = log_level == 'DEBUG'
        
        # 如果是詳細日誌模式，記錄請求信息
        if detailed_logging:
            logger.debug(f"處理請求: {request.method} {request.path}")
            logger.debug(f"請求頭: {dict(request.headers)}")
            logger.debug(f"Cookies: {request.COOKIES}")
        else:
            logger.info(f"處理請求: {request.method} {request.path}")
        
        # 檢查是否是靜態文件請求
        if request.path.startswith('/static/') or request.path.startswith('/media/'):
            logger.debug("靜態文件請求，跳過認證")
            return self.get_response(request)
            
        # 檢查是否是登入或注銷請求
        if request.path in ['/auth/login/', '/auth/callback/']:
            logger.debug(f"認證相關路徑 {request.path}，跳過認證")
            return self.get_response(request)
        
        # 檢查是否是外部系統回調 API（不需要認證，使用簽名驗證）
        # 這些 API 通常用於接收來自其他系統的回調（如審批中心 APS）
        auth_exempt_patterns = getattr(settings, 'SSO_AUTH_EXEMPT_PATTERNS', [
            '/api/callback/',  # 通用回調 API
            '/api/webhooks/',  # Webhook API
        ])
        for pattern in auth_exempt_patterns:
            if pattern in request.path:
                logger.debug(f"外部回調請求 {request.path}（匹配 {pattern}），跳過認證")
                return self.get_response(request)
            
        # 從 cookie 或 header 中獲取 token
        token = request.COOKIES.get('auth_access_token')
        if not token:
            token = request.headers.get('Authorization')
            logger.debug("從 Authorization 頭獲取 token")
        else:
            logger.debug("從 cookie 獲取 token")
        
        if not token:
            logger.warning("未找到 token，請求頭和 cookie 中都沒有")
            auth_requests.labels(status='no_token').inc()
            request.user = AnonymousUser()
            
            # 如果不是 API 請求，重定向到登錄頁面
            if not request.path.startswith('/api/'):
                # 檢查是否為首頁請求，如果是，允許訪問（讓視圖決定是否需要認證）
                if request.path == '/' and getattr(settings, 'DEBUG', False):
                    logger.debug("允許未認證用戶訪問首頁（調試模式）")
                    return self.get_response(request)
                
                next_url = quote(request.get_full_path())
                # 檢查是否存在重定向循環標記
                if 'from_sso' in request.GET:
                    logger.warning("檢測到重定向循環，使用403響應")
                    messages.error(request, '登入過程發生錯誤：重定向循環')
                    return render(request, 'portal/403.html', status=403)
                    
                try:
                    redirect_url = reverse('portal:login') + f"?next={next_url}"
                    logger.info(f"重定向到登錄頁面: {redirect_url}")
                    return redirect(redirect_url)
                except Exception as e:
                    logger.error(f"重定向到登錄頁面時發生錯誤: {str(e)}")
                    # 如果無法重定向到登錄頁面，顯示錯誤提示
                    return HttpResponse(
                        "系統配置錯誤：無法找到登錄頁面。請聯繫管理員。",
                        content_type="text/html",
                        status=500
                    )
                
            return self.get_response(request)
            
        try:
            # 如果是從 header 中獲取的 token，需要去掉 'Bearer ' 前綴
            if token.startswith('Bearer '):
                token_value = token.split(' ')[1]
                logger.debug("從 Bearer token 中提取值")
            else:
                token_value = token
                logger.debug("使用原始 token 值")
                
            logger.debug(f"驗證 token: {token_value[:10]}...")
            
            # 使用新的緩存函數檢查緩存中是否有此 token 的驗證結果
            cached_user = get_token_verification_cache(token_value)
            
            if cached_user:
                logger.debug(f"使用快取的 token 驗證結果，用戶: {cached_user.username}")
                request.user = cached_user
                auth_requests.labels(status='cache_hit').inc()
                return self.get_response(request)
            
            # 從設置中獲取超時設置
            request_timeout = getattr(settings, 'SSO_REQUEST_TIMEOUT', 5)
            
            # 添加更詳細的日誌，記錄 SSO 服務 URL
            sso_verify_url = f"{settings.SSO_SERVICE['URL']}{settings.SSO_SERVICE['TOKEN_VERIFY_URL']}"
            logger.debug(f"即將連接 SSO 服務 URL: {sso_verify_url}")
            
            # 如果快取中沒有，則進行驗證
            verify_response = self.sso_session.post(
                sso_verify_url,
                json={'token': token_value},
                verify=settings.SSO_SERVICE['VERIFY_SSL'],
                timeout=request_timeout
            )
            
            logger.debug(f"SSO 響應狀態: {verify_response.status_code}")
            if detailed_logging:
                logger.debug(f"SSO 響應內容: {verify_response.text}")
            
            if verify_response.status_code == 200:
                user_data = verify_response.json()
                logger.info(f"Token 驗證成功，用戶: {user_data.get('username', 'unknown')}")
                
                # 創建用戶對象，使用統一的 User 類
                user = User(user_data)
                # 保存 token 到用戶對象中，以便後續權限檢查使用
                user.token = token_value
                request.user = user
                
                # 從設置中獲取緩存過期時間
                token_cache_ttl = getattr(settings, 'TOKEN_VERIFICATION_CACHE_TTL', 300)
                
                # 使用新的緩存函數將用戶對象存入快取
                set_token_verification_cache(token_value, user, token_cache_ttl)
                logger.debug(f"用戶信息已存入快取，過期時間: {token_cache_ttl}秒")
                
                auth_requests.labels(status='success').inc()
            elif verify_response.status_code == 401:
                logger.warning(f"Token 已過期: {verify_response.text}")
                auth_requests.labels(status='expired').inc()
                request.user = AnonymousUser()
                
                # 使用 TokenExpiredError 異常
                error = TokenExpiredError()
                
                # 如果不是 API 請求，重定向到登錄頁面
                if not request.path.startswith('/api/'):
                    next_url = quote(request.get_full_path())
                    redirect_url = f"{settings.SSO_SERVICE['URL']}?next={next_url}"
                    logger.info(f"Token 過期，重定向到 SSO 登錄頁面: {redirect_url}")
                    return redirect(redirect_url)
                    
                return JsonResponse({
                    'code': error.code,
                    'message': error.message
                }, status=401)
            else:
                logger.error(f"Token 驗證失敗: HTTP {verify_response.status_code}, 響應內容: {verify_response.text}")
                auth_requests.labels(status='invalid').inc()
                request.user = AnonymousUser()
                
                # 使用 TokenError 異常
                error = TokenError()
                
                # 如果不是 API 請求，重定向到登錄頁面
                if not request.path.startswith('/api/'):
                    next_url = quote(request.get_full_path())
                    redirect_url = f"{settings.SSO_SERVICE['URL']}?next={next_url}"
                    logger.info(f"Token 無效，重定向到 SSO 登錄頁面: {redirect_url}")
                    return redirect(redirect_url)
                    
                return JsonResponse({
                    'code': error.code,
                    'message': error.message
                }, status=401)
                
        except requests.RequestException as e:
            logger.error(f"SSO 服務連接錯誤: {str(e)}")
            auth_requests.labels(status='error').inc()
            request.user = AnonymousUser()
            
            # 如果不是 API 請求，重定向到登錄頁面
            if not request.path.startswith('/api/'):
                next_url = quote(request.get_full_path())
                redirect_url = f"{settings.SSO_SERVICE['URL']}?next={next_url}"
                logger.info(f"SSO 服務錯誤，重定向到登錄頁面: {redirect_url}")
                return redirect(redirect_url)
                
            return JsonResponse({
                'code': 'sso_service_error',
                'message': 'SSO service is temporarily unavailable'
            }, status=503)
        except Exception as e:
            logger.error(f"Token 驗證過程中發生意外錯誤: {str(e)}", exc_info=True)
            auth_requests.labels(status='error').inc()
            request.user = AnonymousUser()
            
            # 如果不是 API 請求，重定向到登錄頁面
            if not request.path.startswith('/api/'):
                next_url = quote(request.get_full_path())
                redirect_url = f"{settings.SSO_SERVICE['URL']}?next={next_url}"
                logger.info(f"發生錯誤，重定向到登錄頁面: {redirect_url}")
                return redirect(redirect_url)
                
            return JsonResponse({
                'code': 'auth_error',
                'message': str(e)
            }, status=500)
        finally:
            auth_latency.observe(time.time() - start_time)
            logger.debug(f"請求處理完成，耗時: {time.time() - start_time:.3f}秒")
            
        return self.get_response(request)