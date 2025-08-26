# LungFung SSO 快速入門指南

本指南幫助您在 5 分鐘內將 LungFung SSO 集成到您的 Django 項目中。

## 🚀 快速安裝（3 步驟）

### 步驟 1: 安裝包

```bash
pip install git+https://github.com/lungfunghk/LungFungInternalMemberSSO.git
```

### 步驟 2: 配置 settings.py

在您的 Django 項目 `settings.py` 文件末尾添加：

```python
# ===== LungFung SSO 配置 =====
from lungfung_sso import configure_sso_settings, add_sso_middleware, add_sso_app

# 根據您的系統選擇對應的配置
configure_sso_settings(globals(), {
    'SSO_SERVER_URL': 'http://sso.lungfung.hk',
    'MODULE_CODE': 'YOUR_SYSTEM_CODE',  # 見下方系統代碼表
    'VERIFY_SSL': True,
    'REQUEST_TIMEOUT': 10,
    'CHILD_MODULES': {
        # 見下方各系統的具體配置
    },
    'PARENT_PERMISSIONS': {
        # 見下方各系統的具體配置
    }
})

add_sso_app(globals())
add_sso_middleware(globals(), 'after_auth')
```

### 步驟 3: 在視圖中使用

```python
from lungfung_sso import ModulePermissionRequiredMixin

class MyView(ModulePermissionRequiredMixin, ListView):
    required_module = 'YOUR_SYSTEM_CODE'
    required_permissions = ['module.action_module']
```

## 📋 各系統配置表

### 台城系統 (TAICHENG)

```python
configure_sso_settings(globals(), {
    'SSO_SERVER_URL': 'http://sso.lungfung.hk',
    'MODULE_CODE': 'TAICHENG',
    'VERIFY_SSL': True,
    'REQUEST_TIMEOUT': 10,
    'CHILD_MODULES': {
        'TRANSFER_ORDER': 'to',
        'SALES_INVOICE': 'sales_invoice',
        'PURCHASE_INVOICE': 'purchase_invoice',
        'SYSTEM': 'system',
    },
    'PARENT_PERMISSIONS': {
        'VIEW_SYSTEM': 'view_taicheng_system',
        'MANAGE_SYSTEM': 'manage_taicheng_system',
    }
})
```

**常用權限：**
- `to.view_to` - 轉貨單查看
- `to.add_to` - 轉貨單添加
- `sales_invoice.view_sales_invoice` - 銷售發票查看
- `purchase_invoice.change_purchase_invoice` - 採購發票修改

### 庫存系統 (STS)

```python
configure_sso_settings(globals(), {
    'SSO_SERVER_URL': 'http://sso.lungfung.hk',
    'MODULE_CODE': 'STS',
    'VERIFY_SSL': True,
    'REQUEST_TIMEOUT': 5,
    'CHILD_MODULES': {
        'INVENTORY': 'inventory',
        'LENDING': 'lending',
        'PAYMENT': 'payment',
        'COMPANY': 'company',
        'LOCATION': 'location',
        'LOGISTICS': 'logistics',
    },
    'PARENT_PERMISSIONS': {
        'VIEW_SYSTEM': 'view_inventory_system',
        'MANAGE_SYSTEM': 'manage_inventory_system',
    }
})
```

**常用權限：**
- `inventory.view_inventory` - 庫存查看
- `inventory.change_inventory` - 庫存修改
- `lending.add_lending` - 借出添加
- `payment.view_payment` - 付款查看

### 會計系統 (ACS)

```python
configure_sso_settings(globals(), {
    'SSO_SERVER_URL': 'http://sso.lungfung.hk',
    'MODULE_CODE': 'ACS',
    'VERIFY_SSL': True,
    'REQUEST_TIMEOUT': 5,
    'CHILD_MODULES': {
        'GENERAL_LEDGER': 'gl',
        'ACCOUNTS_PAYABLE': 'ap',
        'ACCOUNTS_RECEIVABLE': 'ar',
        'FIXED_ASSETS': 'fa',
        'REPORTS': 'reports',
        'BUDGET': 'budget',
    },
    'PARENT_PERMISSIONS': {
        'VIEW_SYSTEM': 'view_accounting_system',
        'MANAGE_SYSTEM': 'manage_accounting_system',
    }
})
```

**常用權限：**
- `gl.view_gl` - 總賬查看
- `ap.add_ap` - 應付賬款添加
- `ar.change_ar` - 應收賬款修改
- `reports.view_reports` - 財務報表查看

### 人力資源系統 (HRS)

```python
configure_sso_settings(globals(), {
    'SSO_SERVER_URL': 'http://sso.lungfung.hk',
    'MODULE_CODE': 'HRS',
    'VERIFY_SSL': True,
    'REQUEST_TIMEOUT': 5,
    'CHILD_MODULES': {
        'EMPLOYEE': 'employee',
        'PAYROLL': 'payroll',
        'ATTENDANCE': 'attendance',
        'LEAVE': 'leave',
        'TRAINING': 'training',
        'PERFORMANCE': 'performance',
    },
    'PARENT_PERMISSIONS': {
        'VIEW_SYSTEM': 'view_hr_system',
        'MANAGE_SYSTEM': 'manage_hr_system',
    }
})
```

**常用權限：**
- `employee.view_employee` - 員工查看
- `payroll.change_payroll` - 薪資修改
- `attendance.view_attendance` - 考勤查看
- `leave.add_leave` - 請假添加

## 💡 視圖使用示例

### 1. 基本列表視圖

```python
from lungfung_sso import ModulePermissionRequiredMixin
from django.views.generic import ListView

class ProductListView(ModulePermissionRequiredMixin, ListView):
    model = Product
    template_name = 'products/list.html'
    
    # 權限配置
    required_module = 'STS'  # 根據您的系統
    required_permissions = ['inventory.view_inventory']
```

### 2. 創建視圖

```python
class ProductCreateView(ModulePermissionRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'products/create.html'
    
    required_module = 'STS'
    required_permissions = ['inventory.add_inventory']
```

### 3. 多權限視圖

```python
class ProductImportView(ModulePermissionRequiredMixin, FormView):
    template_name = 'products/import.html'
    form_class = ImportForm
    
    required_module = 'STS'
    required_permissions = [
        'inventory.add_inventory',    # 需要添加權限
        'inventory.change_inventory'  # 需要修改權限
    ]
```

### 4. 函數視圖使用

```python
from lungfung_sso import module_permission_required

@module_permission_required(('inventory', 'view'))
def product_list(request):
    products = Product.objects.all()
    return render(request, 'products/list.html', {'products': products})

@module_permission_required(('inventory', 'add'), ('inventory', 'change'))
def product_import(request):
    # 需要添加和修改權限
    return render(request, 'products/import.html')
```

### 5. 在視圖中動態檢查權限

```python
from lungfung_sso import check_permission

def dashboard(request):
    context = {
        'can_view_inventory': check_permission(request.user, 'STS', ['inventory.view_inventory']),
        'can_manage_orders': check_permission(request.user, 'TAICHENG', ['to.change_to']),
        'is_system_admin': check_permission(request.user, 'STS', ['manage_inventory_system']),
    }
    return render(request, 'dashboard.html', context)
```

## 🔧 常見權限模式

### 標準 CRUD 權限

```python
# 查看權限
required_permissions = ['module.view_module']

# 創建權限
required_permissions = ['module.add_module']

# 編輯權限
required_permissions = ['module.change_module']

# 刪除權限
required_permissions = ['module.delete_module']

# 完整管理權限
required_permissions = [
    'module.view_module',
    'module.add_module',
    'module.change_module',
    'module.delete_module'
]
```

### 系統級權限

```python
# 系統查看權限（可以查看所有子模組）
required_permissions = ['view_system_name_system']

# 系統管理權限（可以管理所有子模組）
required_permissions = ['manage_system_name_system']
```

## 🐛 快速故障排除

### 1. 導入錯誤

**錯誤：** `No module named 'lungfung_sso'`

**解決：**
```bash
pip install git+https://github.com/lungfunghk/LungFungInternalMemberSSO.git
```

### 2. 權限被拒絕

**檢查：**
1. 確認用戶已登錄
2. 確認權限名稱正確
3. 檢查 SSO 服務器連接

**調試：**
```python
# 在視圖中添加調試信息
from lungfung_sso import check_permission
print(f"用戶權限: {check_permission(request.user, 'YOUR_MODULE', ['your_permission'])}")
```

### 3. Django 設置錯誤

**確認 INSTALLED_APPS 包含：**
```python
INSTALLED_APPS = [
    # ... 其他應用
    'lungfung_sso',
]
```

## 📚 更多資源

- [完整集成指南](../INTEGRATION_GUIDE.md)
- [API 文檔](../README.md)
- [GitHub 倉庫](https://github.com/lungfunghk/LungFungInternalMemberSSO)

## ❓ 需要幫助？

如果遇到問題：

1. 檢查 [GitHub Issues](https://github.com/lungfunghk/LungFungInternalMemberSSO/issues)
2. 查看完整的集成指南
3. 聯繫 LungFung IT 團隊

---

**🎉 恭喜！您已經成功集成 LungFung SSO 服務！**
