# LungFung SSO 認證模組

這是一個 Django 包，為 LungFung 項目提供統一的 SSO（單點登錄）認證功能。

## 功能特點

- 🔐 統一的 SSO 認證服務
- 🛡️ 動態權限檢查和管理
- 🚀 支持多項目共享
- ⚙️ 靈活的配置選項
- 📦 易於安裝和使用
- 🔄 智能緩存機制

## 安裝

### 開發模式安裝（推薦）

```bash
# 在項目根目錄
pip install -e .

# 或者從其他項目安裝
pip install -e /path/to/lungfung-sso
```

### 在 requirements.txt 中使用

```txt
# 本地開發包
-e ../lungfung-sso

# 或者指定絕對路徑
-e /path/to/lungfung-sso
```

## 快速開始

### 1. 添加到 Django 設置

```python
# settings.py
from lungfung_sso import configure_sso_settings, add_sso_middleware, add_sso_app
import os

# 配置 SSO 設置
configure_sso_settings(globals(), {
    'SSO_SERVER_URL': os.getenv('SSO_SERVER_URL', 'http://localhost:8000'),
    'MODULE_CODE': 'TAICHENG',  # 你的模組代碼
    'VERIFY_SSL': not DEBUG,
    'REQUEST_TIMEOUT': 5,
    'CHILD_MODULES': {
        'TRANSFER_ORDER': 'to',
        'SYSTEM': 'system',
        'SALES_INVOICE': 'sales_invoice',
    },
    'PARENT_PERMISSIONS': {
        'VIEW_SYSTEM': 'view_taicheng_system',
        'MANAGE_SYSTEM': 'manage_taicheng_system',
    }
})

# 添加 SSO 應用
add_sso_app(globals())

# 添加 SSO 中間件
add_sso_middleware(globals(), 'after_auth')
```

### 2. 在視圖中使用權限檢查

#### 基於類的視圖

```python
from lungfung_sso import ModulePermissionRequiredMixin
from django.views.generic import ListView

class MyListView(ModulePermissionRequiredMixin, ListView):
    template_name = 'my_template.html'
    model = MyModel
    
    # SSO 權限配置
    required_module = 'TAICHENG'
    required_permissions = ['view_sales_invoice']
```

#### 裝飾器方式

```python
from lungfung_sso import module_permission_required

@module_permission_required(('to', 'view'), ('system', 'manage'))
def my_view(request):
    return render(request, 'my_template.html')
```

#### 函數式權限檢查

```python
from lungfung_sso import check_permission

def my_view(request):
    if check_permission(request.user, 'TAICHENG', ['view_sales_invoice']):
        # 用戶有權限
        return render(request, 'my_template.html')
    else:
        # 用戶無權限
        return HttpResponseForbidden()
```

## 配置選項

### SSO 服務配置

```python
sso_config = {
    'SSO_SERVER_URL': 'http://your-sso-server.com',
    'MODULE_CODE': 'YOUR_MODULE',  # 你的模組代碼
    'VERIFY_SSL': True,            # 是否驗證 SSL 證書
    'REQUEST_TIMEOUT': 5,          # 請求超時時間（秒）
}
```

### 模組配置

```python
sso_config = {
    'CHILD_MODULES': {
        'INVENTORY': 'inventory',      # 庫存模組
        'SALES': 'sales',             # 銷售模組
        'PURCHASE': 'purchase',       # 採購模組
    }
}
```

### 權限配置

```python
sso_config = {
    'PARENT_PERMISSIONS': {
        'VIEW_SYSTEM': 'view_your_system',
        'MANAGE_SYSTEM': 'manage_your_system',
    },
    'CHILD_PERMISSION_TYPES': {
        'VIEW': 'view',
        'ADD': 'add',
        'CHANGE': 'change',
        'DELETE': 'delete',
    }
}
```

## API 參考

### 主要類和函數

#### `ModulePermissionRequiredMixin`
用於基於類的視圖的權限檢查 Mixin。

```python
class MyView(ModulePermissionRequiredMixin, ListView):
    required_module = 'MODULE_NAME'
    required_permissions = ['permission1', 'permission2']
```

#### `check_permission(user, module, permissions)`
檢查用戶是否具有指定模組的權限。

**參數：**
- `user`: Django 用戶對象
- `module`: 模組名稱
- `permissions`: 權限列表（字符串或列表）

**返回：** `bool` - 是否具有權限

#### `module_permission_required(*permissions)`
權限檢查裝飾器。

```python
@module_permission_required(('module', 'action'), 'permission_string')
def my_view(request):
    pass
```

### 設置助手函數

#### `configure_sso_settings(settings_dict, sso_config)`
配置 SSO 相關的 Django 設置。

#### `add_sso_middleware(settings_dict, position='before_auth')`
添加 SSO 中間件到 MIDDLEWARE 設置。

#### `add_sso_app(settings_dict)`
添加 SSO 應用到 INSTALLED_APPS。

## 權限系統

### 權限格式

- **父模組權限**：直接使用權限名稱，如 `view_system`
- **子模組權限**：格式為 `module.action_module`，如 `inventory.view_inventory`

### 權限層級

1. **超級用戶**：擁有所有權限
2. **系統管理權限**：擁有所有子模組的所有權限
3. **系統查看權限**：擁有所有子模組的查看權限
4. **具體模組權限**：只擁有特定模組的特定權限

## 緩存機制

系統使用 Django 緩存框架來提高性能：

- 用戶權限數據緩存 300 秒（可配置）
- 令牌驗證結果緩存
- 自動緩存失效機制

## 日誌記錄

系統提供詳細的日誌記錄：

```python
# 在 settings.py 中配置日誌級別
LOGGING = {
    'loggers': {
        'lungfung_sso': {
            'level': 'INFO',  # 或 'DEBUG' 獲取更詳細的日誌
        },
    },
}
```

## 錯誤處理

系統提供專門的異常類：

- `SSOException`: SSO 基礎異常
- `SSOAuthenticationError`: 認證錯誤
- `SSOPermissionError`: 權限錯誤
- `SSOServiceError`: 服務錯誤
- `TokenError`: 令牌錯誤
- `TokenExpiredError`: 令牌過期錯誤
- `PermissionDeniedError`: 權限拒絕錯誤

## 測試

```bash
# 檢查包是否正確安裝
pip list | grep lungfung-sso

# 測試導入
python -c "import lungfung_sso; print(lungfung_sso.__version__)"

# 運行 Django 檢查
python manage.py check

# 啟動開發服務器
python manage.py runserver
```

## 開發

### 項目結構

```
lungfung-sso/
├── src/
│   └── lungfung_sso/
│       ├── __init__.py           # 包初始化和導出
│       ├── apps.py               # Django 應用配置
│       ├── authentication.py    # SSO 認證服務
│       ├── cache.py             # 緩存功能
│       ├── exceptions.py        # 自定義異常
│       ├── log_format.py        # 日誌格式
│       ├── middleware.py        # JWT 認證中間件
│       ├── models.py            # 用戶模型
│       ├── permissions.py       # 權限控制
│       ├── settings_helper.py   # 設置助手
│       ├── urls.py              # URL 配置
│       └── views.py             # 視圖（目前為空）
├── pyproject.toml               # 項目配置
├── README.md                    # 說明文檔
└── docs/                        # 文檔目錄
```

### 版本更新

1. 更新 `src/lungfung_sso/__init__.py` 中的版本號
2. 更新 `pyproject.toml` 中的版本號
3. 重新安裝：`pip install -e . --force-reinstall`

## 許可證

MIT License

## 支持

如有問題或建議，請聯繫 LungFung IT 團隊。
