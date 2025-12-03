# LungFung SSO 客戶端模組

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Django 5.0+](https://img.shields.io/badge/Django-5.0+-green.svg)](https://www.djangoproject.com/)
[![Version](https://img.shields.io/badge/Version-1.0.3-brightgreen.svg)]()

龍豐 SSO 客戶端模組，為 Django 子系統提供統一的身份認證與權限管理。

---

## 目錄

- [快速入門](#快速入門)
- [配置詳解](#配置詳解)
- [權限模型](#權限模型)
- [視圖使用](#視圖使用)
- [用戶適配器](#用戶適配器)
- [API 參考](#api-參考)
- [故障排除](#故障排除)

---

## 快速入門

### 1. 安裝

```bash
# 從 GitHub 安裝
pip install git+https://github.com/lungfunghk/LungFungInternalMemberSSO.git

# 或添加到 requirements.txt
git+https://github.com/lungfunghk/LungFungInternalMemberSSO.git
```

### 2. 配置 settings.py

在 `settings.py` 文件末尾添加：

```python
import os
from lungfung_sso import configure_sso_settings, add_sso_middleware, add_sso_app

# ===== SSO 配置 =====
configure_sso_settings(globals(), {
    'SSO_SERVER_URL': os.getenv('SSO_SERVER_URL', 'https://lfmember.lungfung.hk'),
    'MODULE_CODE': 'YOUR_SYSTEM_CODE',  # 替換為你的系統代碼
    'VERIFY_SSL': not DEBUG,
    'REQUEST_TIMEOUT': 10,
    'CHILD_MODULES': {
        # 定義你的子模組
        'MODULE_NAME': 'module_code',
    },
    'PARENT_PERMISSIONS': {
        'VIEW_SYSTEM': 'view_your_system',
        'MANAGE_SYSTEM': 'manage_your_system',
    }
})

add_sso_app(globals())
add_sso_middleware(globals(), 'after_auth')
```

### 3. 在視圖中使用

```python
from lungfung_sso import ModulePermissionRequiredMixin
from django.views.generic import ListView

class MyListView(ModulePermissionRequiredMixin, ListView):
    model = MyModel
    template_name = 'my_list.html'
    
    required_module = 'YOUR_SYSTEM_CODE'
    required_permissions = ['module_code.view_module_code']
```

**完成！** 你的視圖現在已受 SSO 權限保護。

---

## 配置詳解

### 完整配置示例

以大正系統 (TCS) 為例：

```python
configure_sso_settings(globals(), {
    # 基本設定
    'SSO_SERVER_URL': os.getenv('SSO_SERVER_URL', 'https://lfmember.lungfung.hk'),
    'MODULE_CODE': 'TCS',
    'VERIFY_SSL': not DEBUG,
    'REQUEST_TIMEOUT': 10,
    
    # 子模組定義
    'CHILD_MODULES': {
        'SALES_INVOICE': 'tc_sales_invoice',
        'CUSTOMER': 'tc_customer',
        'PAYMENT_TERMS': 'tc_payment_terms',
        'NAV_INTEGRATION': 'tc_nav_integration',
        'SYSTEM': 'tc_system_monitor',
    },
    
    # 系統級權限
    'PARENT_PERMISSIONS': {
        'VIEW_SYSTEM': 'view_taicheng_system',
        'MANAGE_SYSTEM': 'manage_taicheng_system',
    },
    
    # 子模組權限類型（可選，有預設值）
    'CHILD_PERMISSION_TYPES': {
        'VIEW': 'view',
        'ADD': 'add',
        'CHANGE': 'change',
        'DELETE': 'delete',
        'SYNC': 'sync',
        'IMPORT': 'import',
        'EXPORT': 'export',
        'APPROVE': 'approve',
    }
})
```

### 環境變量

| 變量 | 說明 | 預設值 |
|------|------|--------|
| `SSO_SERVER_URL` | SSO 服務器地址 | `https://lfmember.lungfung.hk` |
| `SSO_VERIFY_SSL` | 是否驗證 SSL | `true` |
| `SSO_REQUEST_TIMEOUT` | 請求超時秒數 | `10` |

---

## 權限模型

### 權限層級結構

```
系統級權限
├── manage_xxx_system  → 自動獲得所有子模組的全部權限
├── view_xxx_system    → 自動獲得所有子模組的查看權限
└── 模組級權限
    ├── module.view_module
    ├── module.add_module
    ├── module.change_module
    ├── module.delete_module
    └── module.special_action_module
```

### 權限繼承規則

| 用戶權限 | 效果 |
|---------|------|
| `manage_xxx_system` | 自動獲得**所有子模組的全部權限** |
| `view_xxx_system` | 自動獲得**所有子模組的查看權限** |
| `is_superuser=True` | 跳過所有權限檢查 |

### 權限命名格式

```python
# 子模組權限格式：module_code.action_module_code
'tc_sales_invoice.view_tc_sales_invoice'
'tc_sales_invoice.add_tc_sales_invoice'
'tc_sales_invoice.change_tc_sales_invoice'
'tc_sales_invoice.delete_tc_sales_invoice'

# 系統級權限
'view_taicheng_system'
'manage_taicheng_system'
```

---

## 視圖使用

### 方式一：Mixin（推薦）

適用於基於類的視圖：

```python
from lungfung_sso import ModulePermissionRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView

class InvoiceListView(ModulePermissionRequiredMixin, ListView):
    model = Invoice
    template_name = 'invoices/list.html'
    
    required_module = 'TCS'
    required_permissions = ['tc_sales_invoice.view_tc_sales_invoice']

class InvoiceCreateView(ModulePermissionRequiredMixin, CreateView):
    model = Invoice
    form_class = InvoiceForm
    template_name = 'invoices/create.html'
    
    required_module = 'TCS'
    required_permissions = ['tc_sales_invoice.add_tc_sales_invoice']

# 多權限要求
class InvoiceImportView(ModulePermissionRequiredMixin, FormView):
    template_name = 'invoices/import.html'
    
    required_module = 'TCS'
    required_permissions = [
        'tc_sales_invoice.add_tc_sales_invoice',
        'tc_sales_invoice.change_tc_sales_invoice'
    ]
```

### 方式二：裝飾器

適用於函數視圖或方法：

```python
from lungfung_sso import module_permission_required

@module_permission_required(('tc_sales_invoice', 'view'))
def invoice_list(request):
    invoices = Invoice.objects.all()
    return render(request, 'invoices/list.html', {'invoices': invoices})

# 多權限
@module_permission_required(('tc_sales_invoice', 'add'), ('tc_sales_invoice', 'change'))
def invoice_import(request):
    return render(request, 'invoices/import.html')
```

### 方式三：動態檢查

在視圖中動態檢查權限：

```python
from lungfung_sso import check_permission

class DashboardView(TemplateView):
    template_name = 'dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # 動態檢查各種權限
        context.update({
            'can_view_invoice': check_permission(user, 'TCS', ['tc_sales_invoice.view_tc_sales_invoice']),
            'can_add_invoice': check_permission(user, 'TCS', ['tc_sales_invoice.add_tc_sales_invoice']),
            'can_sync': check_permission(user, 'TCS', ['tc_nav_integration.sync_tc_nav_integration']),
            'is_admin': check_permission(user, 'TCS', ['manage_taicheng_system']),
        })
        return context
```

### 在模板中使用

```html
<div class="toolbar">
    {% if can_add_invoice %}
        <a href="{% url 'invoice:create' %}" class="btn btn-primary">新增發票</a>
    {% endif %}
    
    {% if can_sync %}
        <button class="btn btn-warning">同步 NAV</button>
    {% endif %}
    
    {% if is_admin %}
        <a href="{% url 'system:settings' %}" class="btn btn-secondary">系統設置</a>
    {% endif %}
</div>
```

---

## 用戶適配器

### 問題背景

SSO 登入後，`request.user` 是 `lungfung_sso.models.User`（普通 Python 類），而非 Django ORM 模型。當模型使用 `ForeignKey('auth.User')` 時，需要轉換。

### 使用 UserAdapter

```python
from lungfung_sso import UserAdapter

class InvoiceCreateView(ModulePermissionRequiredMixin, CreateView):
    model = Invoice
    
    def form_valid(self, form):
        # 將 SSO User 轉換為 Django User
        form.instance.created_by = UserAdapter.get_or_create_django_user(self.request.user)
        return super().form_valid(form)
```

### UserAdapter API

| 方法 | 說明 |
|------|------|
| `get_or_create_django_user(sso_user)` | 根據 SSO 用戶獲取或創建 Django 用戶 |
| `get_user_display_name(user)` | 獲取用戶顯示名稱 |
| `is_sso_user(user)` | 檢查是否為 SSO 用戶 |
| `get_user_info_dict(user)` | 獲取用戶信息字典（適用於 JSONField） |

---

## API 參考

### 主要導入

```python
from lungfung_sso import (
    # 配置助手
    configure_sso_settings,
    add_sso_middleware,
    add_sso_app,
    
    # 權限控制
    ModulePermissionRequiredMixin,
    module_permission_required,
    check_permission,
    SSOPermission,
    
    # 用戶相關
    User,
    UserAdapter,
    
    # 認證
    JWTAuthenticationMiddleware,
    SSOAuthentication,
    
    # 緩存
    cache_user_data,
    invalidate_user_cache,
    
    # 異常
    SSOException,
    SSOAuthenticationError,
    SSOPermissionError,
    TokenError,
    TokenExpiredError,
    PermissionDeniedError,
)
```

### 權限類

#### ModulePermissionRequiredMixin

```python
class MyView(ModulePermissionRequiredMixin, ListView):
    required_module = 'SYSTEM_CODE'      # 系統代碼
    required_permissions = ['perm1']      # 所需權限列表
```

#### check_permission

```python
check_permission(
    user,           # 用戶對象
    module,         # 系統代碼
    permissions     # 權限列表（字符串或列表）
) -> bool
```

#### module_permission_required

```python
@module_permission_required(
    ('module', 'action'),   # 元組格式
    ('module2', 'action2')  # 可多個
)
def my_view(request):
    pass
```

---

## 故障排除

### 1. 導入錯誤

**錯誤：** `No module named 'lungfung_sso'`

**解決：**
```bash
pip install git+https://github.com/lungfunghk/LungFungInternalMemberSSO.git
```

### 2. 權限被拒絕

**檢查：**
1. 用戶是否已登錄
2. 權限名稱是否正確（格式：`module.action_module`）
3. SSO 服務器是否可連接

**調試：**
```python
# 查看用戶所有權限
print(request.user.get_all_permissions())

# 檢查特定權限
from lungfung_sso import check_permission
print(check_permission(request.user, 'TCS', ['tc_sales_invoice.view_tc_sales_invoice']))
```

### 3. ForeignKey 錯誤

**錯誤：** `Cannot assign "<lungfung_sso.models.User>": "Model.user" must be a "User" instance.`

**解決：** 使用 UserAdapter
```python
from lungfung_sso import UserAdapter
model.user = UserAdapter.get_or_create_django_user(request.user)
```

### 4. SSO 連接失敗

**檢查：**
1. `SSO_SERVER_URL` 配置是否正確
2. 網絡是否可達
3. SSL 配置是否正確

**環境變量：**
```bash
SSO_SERVER_URL=https://lfmember.lungfung.hk
SSO_VERIFY_SSL=true
SSO_REQUEST_TIMEOUT=10
```

### 5. 緩存問題

權限更新後未生效：

```python
from lungfung_sso import invalidate_user_cache
invalidate_user_cache(user.id)
```

---

## 版本歷史

### v1.0.3 (2025-12)
- 新增 `UserAdapter` 用戶適配器
- 改進權限繼承邏輯文檔

### v1.0.2 (2025-12)
- 完善延遲導入機制
- 優化異常處理

### v1.0.0 (2025-03)
- 初始發布版本
- 完整的 SSO 認證功能
- 支持 Django 5.0+

---

## 授權

版權所有 © 2025 龍豐藥業集團有限公司

本軟件僅供龍豐藥業集團內部使用。
