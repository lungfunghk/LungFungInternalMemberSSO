# LungFung SSO 集成指南

本指南詳細説明如何在 LungFung 的各個 Django 子項目中集成 SSO 服務。

## 📋 目錄

1. [快速開始](#快速開始)
2. [詳細安裝步驟](#詳細安裝步驟)
3. [系統配置指南](#系統配置指南)
4. [權限配置詳解](#權限配置詳解)
5. [視圖中的使用方式](#視圖中的使用方式)
6. [遷移現有項目](#遷移現有項目)
7. [故障排除](#故障排除)

## 🚀 快速開始

### 1. 安裝 SSO 包

```bash
# 從 GitHub 安裝
pip install git+https://github.com/lungfunghk/LungFungInternalMemberSSO.git

# 或者本地開發模式安裝
pip install -e git+https://github.com/lungfunghk/LungFungInternalMemberSSO.git#egg=lungfung-sso
```

### 2. 基本配置

在您的 Django 項目 `settings.py` 中：

```python
from lungfung_sso import configure_sso_settings, add_sso_middleware, add_sso_app

# 配置 SSO 設置
configure_sso_settings(globals(), {
    'SSO_SERVER_URL': 'http://sso.lungfung.hk',
    'MODULE_CODE': 'YOUR_MODULE',  # 替換為您的系統模組代碼
    'VERIFY_SSL': True,
    'REQUEST_TIMEOUT': 10,
    'CHILD_MODULES': {
        # 定義您的子模組
        'MODULE1': 'code1',
        'MODULE2': 'code2',
    },
    'PARENT_PERMISSIONS': {
        'VIEW_SYSTEM': 'view_your_system',
        'MANAGE_SYSTEM': 'manage_your_system',
    }
})

# 添加 SSO 應用和中間件
add_sso_app(globals())
add_sso_middleware(globals(), 'after_auth')
```

### 3. 在視圖中使用

```python
from lungfung_sso import ModulePermissionRequiredMixin, module_permission_required

# 方式 1: Mixin 方式（推薦）
class MyListView(ModulePermissionRequiredMixin, ListView):
    required_module = 'YOUR_MODULE'
    required_permissions = ['module1.view_module1']

# 方式 2: 裝飾器方式
class MyView(ListView):
    @module_permission_required(('module1', 'view'))
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
```

## 📦 詳細安裝步驟

### 1. 通過 requirements.txt 安裝

在您的項目 `requirements.txt` 中添加：

```txt
# LungFung SSO 服務
git+https://github.com/lungfunghk/LungFungInternalMemberSSO.git

# 或者指定版本
git+https://github.com/lungfunghk/LungFungInternalMemberSSO.git@v1.0.0
```

然後安裝：

```bash
pip install -r requirements.txt
```

### 2. 驗證安裝

```bash
# 檢查包是否安裝
pip list | grep lungfung-sso

# 測試導入
python -c "import lungfung_sso; print(lungfung_sso.__version__)"
```

## ⚙️ 系統配置指南

### 台城系統 (TAICHENG)

```python
configure_sso_settings(globals(), {
    'SSO_SERVER_URL': 'http://sso.lungfung.hk',
    'MODULE_CODE': 'TAICHENG',
    'VERIFY_SSL': True,
    'REQUEST_TIMEOUT': 10,
    'CHILD_MODULES': {
        'TRANSFER_ORDER': 'to',           # 轉貨單模組
        'SALES_INVOICE': 'sales_invoice', # 銷售發票模組
        'PURCHASE_INVOICE': 'purchase_invoice', # 採購發票模組
        'SYSTEM': 'system',               # 系統管理模組
    },
    'PARENT_PERMISSIONS': {
        'VIEW_SYSTEM': 'view_taicheng_system',
        'MANAGE_SYSTEM': 'manage_taicheng_system',
    }
})
```

**使用示例：**
```python
# 轉貨單列表視圖
class TransferOrderListView(ModulePermissionRequiredMixin, ListView):
    required_module = 'TAICHENG'
    required_permissions = ['to.view_to']

# 銷售發票導入視圖
class SalesInvoiceImportView(ModulePermissionRequiredMixin, FormView):
    required_module = 'TAICHENG'
    required_permissions = ['sales_invoice.add_sales_invoice']
```

### 庫存系統 (STS - Stock Taking System)

```python
configure_sso_settings(globals(), {
    'SSO_SERVER_URL': 'http://sso.lungfung.hk',
    'MODULE_CODE': 'STS',
    'VERIFY_SSL': True,
    'REQUEST_TIMEOUT': 5,
    'CHILD_MODULES': {
        'INVENTORY': 'inventory',   # 庫存管理
        'LENDING': 'lending',       # 借出管理
        'PAYMENT': 'payment',       # 付款管理
        'COMPANY': 'company',       # 公司管理
        'LOCATION': 'location',     # 地點管理
        'LOGISTICS': 'logistics',   # 物流管理
    },
    'PARENT_PERMISSIONS': {
        'VIEW_SYSTEM': 'view_inventory_system',
        'MANAGE_SYSTEM': 'manage_inventory_system',
    }
})
```

**使用示例：**
```python
# 庫存查看視圖
class InventoryListView(ModulePermissionRequiredMixin, ListView):
    required_module = 'STS'
    required_permissions = ['inventory.view_inventory']

# 借出管理視圖
class LendingManageView(ModulePermissionRequiredMixin, FormView):
    required_module = 'STS'
    required_permissions = ['lending.change_lending', 'lending.add_lending']
```

### 會計系統 (ACS - Accounting System)

```python
configure_sso_settings(globals(), {
    'SSO_SERVER_URL': 'http://sso.lungfung.hk',
    'MODULE_CODE': 'ACS',
    'VERIFY_SSL': True,
    'REQUEST_TIMEOUT': 5,
    'CHILD_MODULES': {
        'GENERAL_LEDGER': 'gl',        # 總賬
        'ACCOUNTS_PAYABLE': 'ap',      # 應付賬款
        'ACCOUNTS_RECEIVABLE': 'ar',   # 應收賬款
        'FIXED_ASSETS': 'fa',          # 固定資產
        'REPORTS': 'reports',          # 財務報表
        'BUDGET': 'budget',            # 預算管理
    },
    'PARENT_PERMISSIONS': {
        'VIEW_SYSTEM': 'view_accounting_system',
        'MANAGE_SYSTEM': 'manage_accounting_system',
    }
})
```

### 人力資源系統 (HRS - Human Resource System)

```python
configure_sso_settings(globals(), {
    'SSO_SERVER_URL': 'http://sso.lungfung.hk',
    'MODULE_CODE': 'HRS',
    'VERIFY_SSL': True,
    'REQUEST_TIMEOUT': 5,
    'CHILD_MODULES': {
        'EMPLOYEE': 'employee',       # 員工管理
        'PAYROLL': 'payroll',         # 薪資管理
        'ATTENDANCE': 'attendance',   # 考勤管理
        'LEAVE': 'leave',             # 請假管理
        'TRAINING': 'training',       # 培訓管理
        'PERFORMANCE': 'performance', # 績效管理
    },
    'PARENT_PERMISSIONS': {
        'VIEW_SYSTEM': 'view_hr_system',
        'MANAGE_SYSTEM': 'manage_hr_system',
    }
})
```

## 🔐 權限配置詳解

### 權限層級結構

1. **超級用戶** - 擁有所有權限
2. **系統管理權限** - 擁有該系統所有子模組的所有權限
3. **系統查看權限** - 擁有該系統所有子模組的查看權限
4. **具體模組權限** - 只擁有特定模組的特定權限

### 權限命名規則

#### 父模組權限格式
```
view_{system_name}_system     # 系統查看權限
manage_{system_name}_system   # 系統管理權限
```

**示例：**
- `view_taicheng_system` - 台城系統查看權限
- `manage_inventory_system` - 庫存系統管理權限

#### 子模組權限格式
```
{module_code}.{action}_{module_code}
```

**示例：**
- `to.view_to` - 轉貨單查看權限
- `inventory.add_inventory` - 庫存添加權限
- `sales_invoice.change_sales_invoice` - 銷售發票修改權限

### 標準權限動作

```python
'CHILD_PERMISSION_TYPES': {
    'VIEW': 'view',       # 查看權限
    'ADD': 'add',         # 添加權限
    'CHANGE': 'change',   # 修改權限
    'DELETE': 'delete',   # 刪除權限
}
```

### 自定義權限動作

您也可以定義自定義的權限動作：

```python
configure_sso_settings(globals(), {
    'MODULE_CODE': 'TAICHENG',
    'CHILD_MODULES': {
        'TRANSFER_ORDER': 'to',
    },
    'CHILD_PERMISSION_TYPES': {
        'VIEW': 'view',
        'ADD': 'add',
        'CHANGE': 'change',
        'DELETE': 'delete',
        'SYNC': 'sync',           # 自定義：同步權限
        'IMPORT': 'import',       # 自定義：導入權限
        'EXPORT': 'export',       # 自定義：導出權限
        'APPROVE': 'approve',     # 自定義：審批權限
    }
})
```

使用自定義權限：
```python
# 轉貨單同步權限檢查
@module_permission_required(('to', 'sync'))
def sync_transfer_orders(request):
    # 同步邏輯
    pass

# 發票審批權限檢查
class InvoiceApprovalView(ModulePermissionRequiredMixin, FormView):
    required_module = 'TAICHENG'
    required_permissions = ['sales_invoice.approve_sales_invoice']
```

## 🎯 視圖中的使用方式

### 方式 1: ModulePermissionRequiredMixin（推薦）

```python
from lungfung_sso import ModulePermissionRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

class ProductListView(ModulePermissionRequiredMixin, ListView):
    """產品列表視圖"""
    model = Product
    template_name = 'products/list.html'
    
    # SSO 權限配置
    required_module = 'TAICHENG'
    required_permissions = ['inventory.view_inventory']

class ProductCreateView(ModulePermissionRequiredMixin, CreateView):
    """產品創建視圖"""
    model = Product
    form_class = ProductForm
    template_name = 'products/create.html'
    
    # SSO 權限配置
    required_module = 'TAICHENG'
    required_permissions = ['inventory.add_inventory']

class ProductUpdateView(ModulePermissionRequiredMixin, UpdateView):
    """產品更新視圖"""
    model = Product
    form_class = ProductForm
    template_name = 'products/update.html'
    
    # SSO 權限配置
    required_module = 'TAICHENG'
    required_permissions = ['inventory.change_inventory']

class ProductDeleteView(ModulePermissionRequiredMixin, DeleteView):
    """產品刪除視圖"""
    model = Product
    template_name = 'products/delete.html'
    success_url = reverse_lazy('products:list')
    
    # SSO 權限配置
    required_module = 'TAICHENG'
    required_permissions = ['inventory.delete_inventory']
```

### 方式 2: @module_permission_required 裝飾器

```python
from lungfung_sso import module_permission_required
from django.views.generic import ListView

class ProductListView(ListView):
    model = Product
    template_name = 'products/list.html'
    
    @module_permission_required(('inventory', 'view'))
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

# 函數視圖使用
@module_permission_required(('inventory', 'add'), ('inventory', 'change'))
def product_import_view(request):
    """產品導入視圖 - 需要添加和修改權限"""
    if request.method == 'POST':
        # 處理導入邏輯
        pass
    return render(request, 'products/import.html')
```

### 方式 3: check_permission 函數

```python
from lungfung_sso import check_permission
from django.http import HttpResponseForbidden

def product_export_view(request):
    """產品導出視圖"""
    # 檢查導出權限
    if not check_permission(request.user, 'TAICHENG', ['inventory.export_inventory']):
        return HttpResponseForbidden('您沒有導出權限')
    
    # 導出邏輯
    # ...
    
    return HttpResponse(export_data, content_type='application/vnd.ms-excel')

def dashboard_view(request):
    """儀表板視圖 - 根據權限顯示不同內容"""
    context = {}
    
    # 檢查各種權限並設置上下文
    context['can_view_inventory'] = check_permission(
        request.user, 'TAICHENG', ['inventory.view_inventory']
    )
    context['can_manage_orders'] = check_permission(
        request.user, 'TAICHENG', ['to.change_to', 'to.add_to']
    )
    context['can_manage_system'] = check_permission(
        request.user, 'TAICHENG', ['manage_taicheng_system']
    )
    
    return render(request, 'dashboard.html', context)
```

### 在模板中使用權限檢查

您可以在視圖中設置權限標誌，然後在模板中使用：

```python
# views.py
def product_list_view(request):
    context = {
        'products': Product.objects.all(),
        'can_add_product': check_permission(request.user, 'TAICHENG', ['inventory.add_inventory']),
        'can_edit_product': check_permission(request.user, 'TAICHENG', ['inventory.change_inventory']),
        'can_delete_product': check_permission(request.user, 'TAICHENG', ['inventory.delete_inventory']),
    }
    return render(request, 'products/list.html', context)
```

```html
<!-- templates/products/list.html -->
<div class="product-actions">
    {% if can_add_product %}
        <a href="{% url 'products:create' %}" class="btn btn-primary">添加產品</a>
    {% endif %}
    
    {% if can_edit_product %}
        <a href="{% url 'products:update' product.id %}" class="btn btn-secondary">編輯</a>
    {% endif %}
    
    {% if can_delete_product %}
        <a href="{% url 'products:delete' product.id %}" class="btn btn-danger">刪除</a>
    {% endif %}
</div>
```

## 🔄 遷移現有項目

### 從 apps.core.permissions 遷移

如果您的項目目前使用 `apps.core.permissions`，遷移非常簡單：

#### 步驟 1: 更新導入語句

**之前：**
```python
from apps.core.permissions import module_permission_required
```

**之後：**
```python
from lungfung_sso import module_permission_required
```

#### 步驟 2: 配置系統設置

在 `settings.py` 中添加配置：

```python
from lungfung_sso import configure_sso_settings, add_sso_middleware, add_sso_app

# 根據您的系統添加相應配置
configure_sso_settings(globals(), {
    'MODULE_CODE': 'YOUR_SYSTEM_CODE',
    'CHILD_MODULES': {
        # 您的子模組
    },
    'PARENT_PERMISSIONS': {
        # 您的父模組權限
    }
})

add_sso_app(globals())
add_sso_middleware(globals(), 'after_auth')
```

#### 步驟 3: 更新 requirements.txt

```txt
# 移除舊的依賴
# apps.core

# 添加新的依賴
git+https://github.com/lungfunghk/LungFungInternalMemberSSO.git
```

#### 步驟 4: 測試和驗證

```bash
# 重新安裝依賴
pip install -r requirements.txt

# 運行測試
python manage.py check

# 啟動服務器測試
python manage.py runserver
```

### 批量更新導入語句

您可以使用以下腳本批量更新導入語句：

```bash
# 在項目根目錄運行
find . -name "*.py" -exec sed -i 's/from apps\.core\.permissions import/from lungfung_sso import/g' {} +
```

## 🛠️ 故障排除

### 常見問題

#### 1. 導入錯誤 "No module named 'lungfung_sso'"

**解決方案：**
```bash
# 確認包已安裝
pip list | grep lungfung-sso

# 重新安裝
pip install git+https://github.com/lungfunghk/LungFungInternalMemberSSO.git
```

#### 2. Django 設置未配置錯誤

**錯誤：**
```
django.core.exceptions.ImproperlyConfigured: Requested setting INSTALLED_APPS, but settings are not configured.
```

**解決方案：**
確保在 Django 應用中使用，並且正確配置了 `INSTALLED_APPS`：

```python
# settings.py
INSTALLED_APPS = [
    # ... 其他應用
    'lungfung_sso',
]
```

#### 3. 權限檢查失敗

**問題：** 用戶有權限但仍然被拒絕訪問

**檢查步驟：**

1. 確認 SSO 服務器配置正確：
```python
# 在 Django shell 中測試
python manage.py shell

from django.conf import settings
print(settings.SSO_SERVICE)
```

2. 檢查權限格式：
```python
from lungfung_sso.permissions import Permission
print(Permission.format_permission('your_module', 'view'))
```

3. 檢查用戶權限數據：
```python
from lungfung_sso import check_permission
# 在視圖中添加調試
print(f"用戶權限檢查結果: {check_permission(request.user, 'YOUR_MODULE', ['your_permission'])}")
```

#### 4. prometheus_client 依賴問題

**解決方案：**
SSO 包已經處理了這個問題，如果沒有安裝 prometheus_client，監控功能會被禁用但不會影響核心功能。

如果需要監控功能：
```bash
pip install prometheus_client
```

### 調試技巧

#### 啟用詳細日誌

```python
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'lungfung_sso': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
```

#### 檢查權限配置

```python
# 在 Django shell 中
from lungfung_sso.permissions import Module, Permission

print("父模組:", Module.get_parent_module())
print("子模組:", Module.get_child_modules())
print("父模組權限:", Permission.get_parent_permissions())
print("子模組權限類型:", Permission.get_child_permission_types())
```

## 📞 支持和幫助

如有問題或需要幫助，請：

1. 檢查 [GitHub Issues](https://github.com/lungfunghk/LungFungInternalMemberSSO/issues)
2. 查看項目文檔和示例
3. 聯繫 LungFung IT 團隊

## 🔄 版本更新

當 SSO 包有更新時：

```bash
# 更新到最新版本
pip install --upgrade git+https://github.com/lungfunghk/LungFungInternalMemberSSO.git

# 或者指定版本
pip install --upgrade git+https://github.com/lungfunghk/LungFungInternalMemberSSO.git@v1.1.0
```

## 📝 最佳實踐

1. **統一權限命名** - 在整個系統中使用一致的權限命名規則
2. **最小權限原則** - 只授予用戶必要的最小權限
3. **權限分層** - 合理使用系統級和模組級權限
4. **測試權限** - 在部署前充分測試權限配置
5. **文檔維護** - 維護權限和模組的文檔
6. **定期審核** - 定期審核和更新權限配置

---

*本指南涵蓋了 LungFung SSO 在各個子系統中的集成方法。如有更新或改進建議，請聯繫開發團隊。*
