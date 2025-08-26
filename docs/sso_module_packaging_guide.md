# LungFung SSO 模組打包指南

## 概述

本指南描述如何將現有的 SSO 功能從項目中的 `apps/core` 模組重構為獨立的可重用 Python 包，使用本地包開發模式。這樣可以讓多個項目共享相同的 SSO 功能，而無需複製源代碼。

## 目標

- 將 SSO 相關功能提取為獨立的 Python 包
- 使用本地包開發模式 (`pip install -e`)
- 讓其他項目可以通過 requirements.txt 安裝和使用
- 保持代碼的可維護性和可重用性

## 項目結構

### 最終目標結構
```
workspace/
├── lungfung-sso/                    # SSO 包項目
│   ├── src/
│   │   └── lungfung_sso/
│   │       ├── __init__.py
│   │       ├── apps.py              # Django App 配置
│   │       ├── authentication.py   # SSO 認證服務
│   │       ├── cache.py            # 緩存功能
│   │       ├── exceptions.py       # 自定義異常
│   │       ├── middleware.py       # JWT 認證中間件
│   │       ├── permissions.py      # 權限控制
│   │       ├── settings_helper.py  # 設置助手
│   │       └── utils.py            # 工具函數
│   ├── pyproject.toml
│   ├── README.md
│   └── tests/
├── LungFungTaicheng/               # 本項目
│   ├── apps/
│   │   └── core/                   # 簡化後只保留項目特定邏輯
│   ├── config/
│   └── requirements.txt            # 包含 lungfung-sso 依賴
└── OtherProject/                   # 其他項目
    ├── apps/
    ├── config/
    └── requirements.txt            # 也可以使用 lungfung-sso
```

## 實施步驟

### 步驟 1：創建 SSO 包項目

```bash
# 在工作區根目錄創建 SSO 包
mkdir lungfung-sso
cd lungfung-sso

# 初始化 Python 項目
uv init .

# 創建包結構
mkdir -p src/lungfung_sso
mkdir tests
```

### 步驟 2：配置 pyproject.toml

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "lungfung-sso"
version = "1.0.0"
description = "LungFung SSO authentication module for Django projects"
authors = [
    {name = "LungFung IT Team", email = "it@lungfung.hk"}
]
readme = "README.md"
license = {text = "MIT"}
requires-python = ">=3.11"
classifiers = [
    "Development Status :: 4 - Beta",
    "Framework :: Django",
    "Framework :: Django :: 5.0",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.11",
]

dependencies = [
    "django>=5.0.0",
    "djangorestframework>=3.15.0",
    "requests>=2.31.0",
    "pyjwt>=2.8.0",
    "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-django>=4.5.0",
    "black>=23.0.0",
    "flake8>=6.0.0",
    "isort>=5.12.0",
]

[project.urls]
Homepage = "https://github.com/lungfung/lungfung-sso"
Repository = "https://github.com/lungfung/lungfung-sso.git"
Issues = "https://github.com/lungfung/lungfung-sso/issues"

[tool.hatch.build.targets.wheel]
packages = ["src/lungfung_sso"]

[tool.black]
line-length = 88
target-version = ['py311']
include = '\.pyi?$'

[tool.isort]
profile = "black"
multi_line_output = 3
line_length = 88
```

### 步驟 3：移動和重構代碼

#### 3.1 創建 Django App 配置

```python
# src/lungfung_sso/apps.py
from django.apps import AppConfig

class LungfungSsoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'lungfung_sso'
    verbose_name = 'LungFung SSO'
    
    def ready(self):
        """當 Django 應用準備就緒時執行"""
        pass
```

#### 3.2 創建包初始化文件

```python
# src/lungfung_sso/__init__.py
"""
LungFung SSO Authentication Module

A Django package providing SSO authentication functionality
for LungFung projects.
"""

__version__ = "1.0.0"
__author__ = "LungFung IT Team"

# 主要組件導入
from .authentication import SSOAuthenticationService
from .middleware import JWTAuthenticationMiddleware  
from .permissions import (
    ModulePermissionRequiredMixin,
    SSOperationPermission,
    check_permission,
)
from .exceptions import (
    SSOException,
    SSOAuthenticationError,
    SSOPermissionError,
    SSOServiceError,
)

# 便捷導入
__all__ = [
    # 版本信息
    '__version__',
    '__author__',
    
    # 核心服務
    'SSOAuthenticationService',
    
    # 中間件
    'JWTAuthenticationMiddleware',
    
    # 權限相關
    'ModulePermissionRequiredMixin',
    'SSOperationPermission', 
    'check_permission',
    
    # 異常類
    'SSOException',
    'SSOAuthenticationError',
    'SSOPermissionError',
    'SSOServiceError',
]

# 包級別配置
default_app_config = 'lungfung_sso.apps.LungfungSsoConfig'
```

#### 3.3 移動現有代碼文件

將以下文件從 `LungFungTaicheng/apps/core/` 複製到 `lungfung-sso/src/lungfung_sso/`：

- `authentication.py`
- `cache.py`  
- `exceptions.py`
- `middleware.py`
- `permissions.py`

#### 3.4 創建設置助手

```python
# src/lungfung_sso/settings_helper.py
"""
Django 設置助手

提供便捷的方法來配置 SSO 相關設置
"""

def configure_sso_settings(settings_dict, sso_config=None):
    """
    配置 SSO 相關的 Django 設置
    
    Args:
        settings_dict: Django settings 字典 (通常是 globals())
        sso_config: SSO 配置字典
    """
    default_config = {
        'SSO_SERVER_URL': 'http://localhost:8000',
        'MODULE_CODE': 'DEFAULT',
        'VERIFY_SSL': True,
        'REQUEST_TIMEOUT': 5,
    }
    
    if sso_config:
        default_config.update(sso_config)
    
    # 設置 SSO 服務配置
    settings_dict['SSO_SERVICE'] = {
        'URL': default_config['SSO_SERVER_URL'],
        'VERIFY_SSL': default_config['VERIFY_SSL'],
        
        # API 端點
        'TOKEN_URL': '/api/auth/token/',
        'TOKEN_REFRESH_URL': '/api/auth/token/refresh/',
        'TOKEN_VERIFY_URL': '/api/auth/verify/',
        'USER_INFO_URL': '/api/auth/user/info/',
        'USER_PROFILE_URL': '/api/auth/user/profile/',
        'USER_PERMISSIONS_URL': '/api/core/permissions/user/',
        'PERMISSION_CHECK_URL': '/api/core/permissions/check/',
        'MODULES_URL': '/api/core/modules/',
        'MODULE_CHECK_URL': '/api/core/modules/check/',
    }
    
    # 設置模組配置
    settings_dict['SSO_MODULES'] = {
        'PARENT_MODULE': default_config['MODULE_CODE'].split('_')[0] if '_' in default_config['MODULE_CODE'] else default_config['MODULE_CODE'],
        'CHILD_MODULES': {},
    }
    
    # 設置權限配置
    settings_dict['SSO_PERMISSIONS'] = {
        'PARENT_PERMISSIONS': {
            'VIEW_SYSTEM': f'view_{default_config["MODULE_CODE"].lower()}_system',
            'MANAGE_SYSTEM': f'manage_{default_config["MODULE_CODE"].lower()}_system',
        },
        'CHILD_PERMISSION_TYPES': {
            'VIEW': 'view',
            'ADD': 'add', 
            'CHANGE': 'change',
            'DELETE': 'delete',
        }
    }
    
    # 請求配置
    settings_dict['SSO_REQUEST_TIMEOUT'] = default_config['REQUEST_TIMEOUT']
    
    return settings_dict

def add_sso_middleware(settings_dict, position='before_auth'):
    """
    添加 SSO 中間件到 MIDDLEWARE 設置
    
    Args:
        settings_dict: Django settings 字典
        position: 'before_auth' 或 'after_auth' 或具體位置索引
    """
    middleware_class = 'lungfung_sso.middleware.JWTAuthenticationMiddleware'
    middleware = settings_dict.get('MIDDLEWARE', [])
    
    if middleware_class in middleware:
        return  # 已經存在
    
    if position == 'before_auth':
        auth_index = None
        for i, mw in enumerate(middleware):
            if 'AuthenticationMiddleware' in mw:
                auth_index = i
                break
        if auth_index is not None:
            middleware.insert(auth_index, middleware_class)
        else:
            middleware.append(middleware_class)
    elif position == 'after_auth':
        auth_index = None
        for i, mw in enumerate(middleware):
            if 'AuthenticationMiddleware' in mw:
                auth_index = i + 1
                break
        if auth_index is not None:
            middleware.insert(auth_index, middleware_class)
        else:
            middleware.append(middleware_class)
    elif isinstance(position, int):
        middleware.insert(position, middleware_class)
    else:
        middleware.append(middleware_class)
    
    settings_dict['MIDDLEWARE'] = middleware

def add_sso_app(settings_dict):
    """
    添加 SSO 應用到 INSTALLED_APPS
    """
    installed_apps = settings_dict.get('INSTALLED_APPS', [])
    sso_app = 'lungfung_sso'
    
    if sso_app not in installed_apps:
        installed_apps.append(sso_app)
        settings_dict['INSTALLED_APPS'] = installed_apps
```

### 步驟 4：安裝開發版本

```bash
# 在 lungfung-sso 目錄中
pip install -e .

# 或者從其他項目目錄安裝
pip install -e /path/to/lungfung-sso
```

### 步驟 5：在項目中使用

#### 5.1 更新 requirements.txt

```txt
# LungFungTaicheng/requirements.txt

# 本地 SSO 包 (開發模式)
-e ../lungfung-sso

# 其他依賴...
Django==5.0.9
djangorestframework==3.15.2
# ...
```

#### 5.2 更新 Django 設置

```python
# LungFungTaicheng/config/settings.py

from lungfung_sso.settings_helper import (
    configure_sso_settings,
    add_sso_middleware,
    add_sso_app,
)

# ... 其他設置 ...

# 應用 SSO 配置
configure_sso_settings(globals(), {
    'SSO_SERVER_URL': os.getenv('SSO_SERVER_URL', 'http://localhost:8000'),
    'MODULE_CODE': 'TAICHENG',
    'VERIFY_SSL': not DEBUG,
})

# 添加 SSO 應用
add_sso_app(globals())

# 添加 SSO 中間件 (會自動插入到適當位置)
add_sso_middleware(globals(), 'after_auth')
```

#### 5.3 在視圖中使用

```python
# LungFungTaicheng/apps/sales_invoice/views.py

from lungfung_sso import ModulePermissionRequiredMixin
from lungfung_sso.permissions import check_permission
from lungfung_sso.authentication import SSOAuthenticationService

class PurchaseInvoiceListView(ModulePermissionRequiredMixin, ListView):
    """採購發票列表視圖"""
    template_name = 'sales_invoice/purchase_invoice_list.html'
    model = PurchaseInvoice
    
    # SSO 權限配置
    required_module = 'TAICHENG'
    required_permissions = ['view_sales_invoice']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 檢查額外權限
        can_sync = check_permission(
            self.request.user, 
            'TAICHENG', 
            'sync_nav_data'
        )
        context['can_sync'] = can_sync
        
        return context
```

### 步驟 6：清理原項目

#### 6.1 簡化 apps/core

移動到 SSO 包後，`apps/core` 只保留項目特定的邏輯：

```python
# LungFungTaicheng/apps/core/__init__.py
# 保持為空或只包含項目特定內容

# LungFungTaicheng/apps/core/models.py
# 只保留項目特定的模型

# LungFungTaicheng/apps/core/views.py  
# 只保留項目特定的視圖
```

#### 6.2 更新導入語句

將所有 SSO 相關的導入更新為使用新包：

```python
# 舊的導入
from apps.core.middleware import JWTAuthenticationMiddleware
from apps.core.permissions import ModulePermissionRequiredMixin

# 新的導入  
from lungfung_sso import JWTAuthenticationMiddleware
from lungfung_sso import ModulePermissionRequiredMixin
```

## 測試和驗證

### 1. 測試包安裝

```bash
# 檢查包是否正確安裝
pip list | grep lungfung-sso

# 測試導入
python -c "import lungfung_sso; print(lungfung_sso.__version__)"
```

### 2. 測試 Django 集成

```bash
# 檢查 Django 應用
python manage.py check

# 運行開發服務器
python manage.py runserver 8004
```

### 3. 功能測試

- 測試 JWT 認證是否正常工作
- 測試權限檢查是否正確
- 測試 SSO 服務調用

## 其他項目使用

### 新項目集成

```bash
# 1. 創建新項目
django-admin startproject NewProject

# 2. 添加 SSO 依賴
echo "-e /path/to/lungfung-sso" >> requirements.txt

# 3. 安裝依賴
pip install -r requirements.txt

# 4. 配置設置
# 在 settings.py 中使用 configure_sso_settings()
```

## 維護和更新

### 版本管理

```bash
# 更新版本號
# 編輯 src/lungfung_sso/__init__.py 和 pyproject.toml

# 重新安裝更新版本
pip install -e /path/to/lungfung-sso --force-reinstall
```

### 代碼同步

當 SSO 包有更新時，所有使用該包的項目會自動獲得更新（使用 -e 安裝的情況下）。

## 優勢

1. **代碼重用**：多個項目可以共享相同的 SSO 功能
2. **維護性**：SSO 功能集中維護，bug 修復和功能改進可以惠及所有項目
3. **一致性**：確保所有項目使用相同版本的 SSO 功能
4. **模組化**：清晰的模組邊界，便於理解和測試
5. **擴展性**：可以輕鬆添加新的 SSO 功能，而不影響現有項目

## 注意事項

1. **路徑管理**：確保所有項目都能正確找到 SSO 包的路徑
2. **依賴版本**：保持 Django 和其他依賴版本的兼容性
3. **配置同步**：當 SSO 包的配置有變化時，需要更新所有使用項目
4. **測試覆蓋**：為 SSO 包編寫完整的測試用例

這個方案提供了一個靈活且易於維護的方式來管理 SSO 功能，同時保持了開發的便利性。
