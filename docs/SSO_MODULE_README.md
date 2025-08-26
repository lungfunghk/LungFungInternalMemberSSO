# 龍豐 SSO 客戶端模組

[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Django 5.0+](https://img.shields.io/badge/Django-5.0+-green.svg)](https://www.djangoproject.com/)
[![DRF 3.14+](https://img.shields.io/badge/DRF-3.14+-red.svg)](https://www.django-rest-framework.org/)
[![License](https://img.shields.io/badge/License-Private-yellow.svg)]()

龍豐 SSO 客戶端模組提供了全面的單點登錄（Single Sign-On）解決方案，可輕鬆集成到任何 Django 子系統中，實現統一的身份認證與權限管理。

## 目錄

- [功能特點](#功能特點)
- [快速安裝](#快速安裝)
- [詳細配置](#詳細配置)
- [使用示例](#使用示例)
- [API 參考](#api-參考)
- [故障排除](#故障排除)
- [開發者工具](#開發者工具)
- [版本歷史](#版本歷史)

## 功能特點

🔐 **全面的身份認證**
- JWT 令牌認證支持
- 令牌自動刷新機制
- 安全的 Cookie 管理
- 認證中間件自動驗證

🛡️ **精細的權限控制**
- 模組化權限架構
- 基於模組與操作的細粒度控制
- 權限裝飾器與權限類
- 超級用戶特權管理

🔄 **高效的緩存機制**
- 令牌驗證結果緩存
- 用戶信息與權限數據緩存
- 可配置的緩存策略
- 緩存失效自動處理

🔍 **健康監控**
- 集成的健康檢查 API
- 各項服務狀態監控
- 可定制的檢查項目
- 監控系統兼容性

⚙️ **高度可配置**
- 豐富的環境變量支持
- 靈活的設置項
- 可自定義的模組與權限
- 多環境部署支持

## 快速安裝

### 1. 複製模組

將 `apps/core` 目錄複製到您的 Django 項目中：

```bash
cp -r apps/core /path/to/your/project/apps/
```

### 2. 安裝依賴

確保您的項目已安裝以下依賴：

```bash
pip install django djangorestframework requests
```

### 3. 添加應用

在 `settings.py` 中添加應用：

```python
INSTALLED_APPS = [
    # ... 其他應用
    'apps.core',
]
```

### 4. 配置中間件

在 `settings.py` 中添加認證中間件：

```python
MIDDLEWARE = [
    # ... 其他中間件
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'apps.core.middleware.JWTAuthenticationMiddleware',  # 添加此行
]
```

### 5. 配置 URLs

在您的主 `urls.py` 中添加 SSO 相關路由：

```python
from django.urls import path, include

urlpatterns = [
    # ... 其他 URL 配置
    path('api/', include('apps.core.urls')),  # 添加此行，包含健康檢查 API
]
```

### 6. 基本配置

在 `settings.py` 中添加必要配置：

```python
# SSO 服務配置
SSO_SERVICE = {
    'URL': os.environ.get('SSO_SERVICE_URL', 'http://localhost:8090'),
    'VERIFY_SSL': False,  # 開發環境設置，生產環境應設為 True
    'TOKEN_VERIFY_URL': '/api/auth/verify/',
    'USER_PERMISSIONS_URL': '/api/auth/permissions/',
}

# 緩存配置
CACHE_KEY_PREFIX = 'your_system_'
TOKEN_VERIFICATION_CACHE_TTL = 300  # 5分鐘
USER_CACHE_TIMEOUT = 300  # 5分鐘
```

## 詳細配置

### SSO 服務配置

```python
SSO_SERVICE = {
    # SSO 服務基礎 URL
    'URL': os.environ.get('SSO_SERVICE_URL', 'http://localhost:8090'),
    
    # 是否驗證 SSL 證書
    'VERIFY_SSL': os.environ.get('SSO_VERIFY_SSL', 'false').lower() == 'true',
    
    # 認證相關端點
    'TOKEN_URL': '/api/auth/token/',
    'TOKEN_REFRESH_URL': '/api/auth/token/refresh/',
    'TOKEN_VERIFY_URL': '/api/auth/verify/',
    
    # 用戶信息相關端點
    'USER_INFO_URL': '/api/auth/user/info/',
    'USER_PROFILE_URL': '/api/auth/user/profile/',
    
    # 權限相關端點
    'USER_PERMISSIONS_URL': '/api/core/permissions/user/',
    'PERMISSION_CHECK_URL': '/api/core/permissions/check/',
    
    # 健康檢查端點
    'HEALTH_CHECK_URL': '/api/health/',
}
```

### 緩存配置

```python
# 緩存鍵配置
CACHE_KEY_PREFIX = os.environ.get('CACHE_KEY_PREFIX', 'your_system_')
CACHE_TYPE_TOKEN = 'token'
CACHE_TYPE_PERMISSIONS = 'permissions'
CACHE_TYPE_USER = 'user'

# 緩存超時設置
TOKEN_VERIFICATION_CACHE_TTL = int(os.environ.get('TOKEN_VERIFICATION_CACHE_TTL', 300))
USER_CACHE_TIMEOUT = int(os.environ.get('USER_CACHE_TIMEOUT', 300))
PERMISSIONS_CACHE_TIMEOUT = int(os.environ.get('PERMISSIONS_CACHE_TIMEOUT', USER_CACHE_TIMEOUT))
```

### 模組與權限配置

```python
# 模組配置
SSO_MODULES = {
    # 父模組
    'PARENT_MODULE': 'YOUR_SYSTEM_CODE',  # 替換為您的系統代碼
    
    # 子模組 - 根據子系統需求擴展
    'CHILD_MODULES': {
        'MODULE1': 'm1',  # 子模組1
        'MODULE2': 'm2',  # 子模組2
    }
}

# 權限配置
SSO_PERMISSIONS = {
    # 父模組權限
    'PARENT_PERMISSIONS': {
        'VIEW_SYSTEM': f'view_{SSO_MODULES["PARENT_MODULE"].lower()}',
        'MANAGE_SYSTEM': f'manage_{SSO_MODULES["PARENT_MODULE"].lower()}',
    },
    
    # 子模組權限類型
    'CHILD_PERMISSION_TYPES': {
        'VIEW': 'view',
        'ADD': 'add',
        'CHANGE': 'change',
        'DELETE': 'delete',
    }
}
```

### 請求配置

```python
# SSO 服務請求配置
SSO_REQUEST_TIMEOUT = int(os.environ.get('SSO_REQUEST_TIMEOUT', 5))  # 秒
SSO_CONNECTION_POOL_SIZE = int(os.environ.get('SSO_CONNECTION_POOL_SIZE', 20))
SSO_MAX_RETRIES = int(os.environ.get('SSO_MAX_RETRIES', 0))

# 日誌配置
SSO_LOGGING_LEVEL = os.environ.get('SSO_LOGGING_LEVEL', 'DEBUG' if DEBUG else 'INFO')
```

### 健康檢查配置

```python
# 健康檢查配置
HEALTH_CHECK_IGNORE_SSO = os.environ.get('HEALTH_CHECK_IGNORE_SSO', 'false').lower() == 'true'
HEALTH_CHECK_IGNORE_CACHE = os.environ.get('HEALTH_CHECK_IGNORE_CACHE', 'false').lower() == 'true'
HEALTH_CHECK_IGNORE_CONFIG = os.environ.get('HEALTH_CHECK_IGNORE_CONFIG', 'false').lower() == 'true'
HEALTH_CHECK_IGNORE_DATABASE = os.environ.get('HEALTH_CHECK_IGNORE_DATABASE', 'false').lower() == 'true'
```

## 使用示例

### 1. 視圖中的權限檢查

#### 基於類的視圖：

```python
from django.views.generic import TemplateView
from apps.core.permissions import module_permission_required, Permission

class DashboardView(TemplateView):
    template_name = 'dashboard.html'
    
    @module_permission_required('PARENT_MODULE', 'VIEW_SYSTEM')
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
```

#### REST API 視圖：

```python
from rest_framework.views import APIView
from rest_framework.response import Response
from apps.core.permissions import SSOPermission

class UserDataAPI(APIView):
    permission_classes = [SSOPermission]
    required_permissions = ['YOUR_SYSTEM_CODE.view_your_system_code']
    
    def get(self, request):
        return Response({
            'username': request.user.username,
            'permissions': request.user.get_all_permissions()
        })
```

### 2. 使用緩存裝飾器

```python
from django.http import JsonResponse
from apps.core.cache import cache_user_data

@cache_user_data(timeout=600)  # 10分鐘緩存
def user_profile(request):
    # request.user_data 已包含緩存的用戶數據
    return JsonResponse({
        'profile': request.user_data['profile'],
        'permissions': request.user_data['permissions']
    })
```

### 3. 健康檢查集成

```python
# 通過 API 檢查系統健康狀態
import requests

def check_subsystem_health():
    response = requests.get('https://your-system.example.com/api/health/')
    
    if response.status_code == 200:
        print("系統正常運行")
        print(f"健康狀態: {response.json()}")
    else:
        print(f"系統狀態異常: {response.status_code}")
        print(f"詳情: {response.json()}")
```

### 4. 手動檢查權限

```python
from django.shortcuts import redirect
from django.contrib import messages

def protected_view(request):
    if not request.user.is_authenticated:
        return redirect('login')
        
    if not request.user.has_perm('MODULE1.view_m1'):
        messages.error(request, '您沒有權限訪問此頁面')
        return redirect('home')
        
    # 有權限的用戶可以訪問的內容
    return render(request, 'protected_template.html')
```

## API 參考

### 模組提供的關鍵類和函數

#### 認證相關

- `JWTAuthenticationMiddleware`: 自動處理 JWT 令牌認證的中間件
- `SSOAuthentication`: Django REST Framework 認證類
- `User`: 統一的用戶模型類，包含權限信息

#### 權限相關

- `Module`: 模組枚舉類，可通過 `Module.MODULE_NAME` 引用配置的模組
- `Permission`: 權限枚舉類，提供權限類型常量
- `SSOPermission`: Django REST Framework 權限類
- `module_permission_required`: 檢查模組權限的裝飾器

#### 緩存相關

- `cache_user_data`: 緩存用戶數據的裝飾器
- `get_token_verification_cache`/`set_token_verification_cache`: 管理令牌緩存
- `get_user_permissions_cache`/`set_user_permissions_cache`: 管理權限緩存
- `invalidate_user_cache`: 使用戶緩存失效

#### 健康檢查相關

- `HealthCheckView`: 提供健康檢查功能的 API 視圖
- `health_check`: 檢查系統健康狀態的函數

#### 異常類

- `TokenError`: 令牌相關錯誤
- `TokenExpiredError`: 令牌過期錯誤
- `PermissionDeniedError`: 權限拒絕錯誤
- `SSOAuthenticationError`: SSO 認證基礎錯誤

## 故障排除

### 無法連接 SSO 服務

**問題**: 應用無法連接到 SSO 服務，出現連接超時或拒絕錯誤。

**解決方案**:
1. 確認 `SSO_SERVICE['URL']` 設置正確
2. 檢查網絡連接和防火牆設置
3. 檢查 SSO 服務是否正常運行
4. 調整 `SSO_REQUEST_TIMEOUT` 增加等待時間

### 令牌驗證失敗

**問題**: 用戶令牌驗證持續失敗。

**解決方案**:
1. 檢查令牌是否已過期
2. 確認 `SSO_SERVICE['TOKEN_VERIFY_URL']` 配置正確
3. 檢查日誌中的具體錯誤信息
4. 清除用戶瀏覽器 cookie，重新登錄

### 權限問題

**問題**: 用戶無法訪問應有權限的頁面。

**解決方案**:
1. 確認 `SSO_MODULES` 和 `SSO_PERMISSIONS` 配置正確
2. 查看用戶實際擁有的權限 (`request.user.get_all_permissions()`)
3. 確認視圖中使用的權限定義正確
4. 檢查 SSO 服務中用戶的權限設置

### 緩存問題

**問題**: 更新的用戶信息或權限未及時反映。

**解決方案**:
1. 使用 `invalidate_user_cache(user_id)` 手動清除緩存
2. 調整 `USER_CACHE_TIMEOUT` 縮短緩存時間
3. 確認 Django 緩存後端配置正確
4. 在開發環境中可將緩存時間設置更短

### 健康檢查顯示服務降級

**問題**: 健康檢查 API 返回 "degraded" 狀態。

**解決方案**:
1. 查看響應中的詳細服務狀態信息
2. 檢查 SSO 服務連接
3. 確認緩存服務正常工作
4. 查看系統日誌獲取更多信息

## 開發者工具

### 模組與權限追蹤

在開發環境中啟用權限追蹤，將詳細的權限檢查過程輸出到日誌：

```python
if DEBUG:
    SSO_LOGGING_LEVEL = 'DEBUG'
    LOGGING['loggers']['apps.core'] = {
        'handlers': ['console'],
        'level': 'DEBUG',
        'propagate': False,
    }
```

### 手動測試指令

測試 SSO 連接和令牌驗證：

```python
python manage.py shell

>>> from apps.core.authentication import SSOAuthentication
>>> auth = SSOAuthentication()
>>> auth._test_sso_connection()  # 測試連接
>>> auth._verify_test_token('your_test_token')  # 測試令牌驗證
```

### 權限導出工具

導出當前配置的所有權限，用於測試和文檔：

```python
python manage.py shell

>>> from apps.core.permissions import Module, Permission
>>> Module.get_child_modules()  # 獲取所有子模組
>>> Permission.get_module_permissions()  # 獲取所有權限類型
```

## 版本歷史

### v1.0.0 (2025-03-27)
- 初始發布版本
- 完整的 SSO 客戶端功能
- 支持 Django 5.0+

### v0.9.5 (2025-03-15)
- 預發布版本
- 完善文檔和錯誤處理
- 添加健康檢查 API

---

## 授權說明

版權所有 © 2025 龍豐藥業集團有限公司

本軟件為龍豐藥業集團內部使用，未經許可不得外泄或用於商業用途。 