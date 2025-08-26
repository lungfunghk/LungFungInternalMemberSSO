# LungFung 各系統 SSO 配置指南

本文檔提供 LungFung 各個子系統的詳細 SSO 配置信息。

## 📖 配置概述

每個 LungFung 子系統都有其特定的：
- **系統代碼 (MODULE_CODE)** - 唯一標識符
- **子模組 (CHILD_MODULES)** - 系統內的功能模組
- **權限配置 (PERMISSIONS)** - 訪問控制設置

## 🏢 系統配置詳情

### 1. 台城系統 (TAICHENG)

**系統描述：** 台城分公司的業務管理系統，主要處理轉貨單、發票等業務流程。

```python
# settings.py
configure_sso_settings(globals(), {
    'SSO_SERVER_URL': 'http://sso.lungfung.hk',
    'MODULE_CODE': 'TAICHENG',
    'VERIFY_SSL': True,
    'REQUEST_TIMEOUT': 10,
    'CHILD_MODULES': {
        'TRANSFER_ORDER': 'to',           # 轉貨單模組
        'SALES_INVOICE': 'sales_invoice', # 銷售發票模組
        'PURCHASE_INVOICE': 'purchase_invoice', # 採購發票模組
        'INVENTORY': 'inventory',         # 庫存管理模組
        'SYSTEM': 'system',               # 系統管理模組
        'REPORTS': 'reports',             # 報表模組
    },
    'PARENT_PERMISSIONS': {
        'VIEW_SYSTEM': 'view_taicheng_system',
        'MANAGE_SYSTEM': 'manage_taicheng_system',
    },
    'CHILD_PERMISSION_TYPES': {
        'VIEW': 'view',
        'ADD': 'add',
        'CHANGE': 'change',
        'DELETE': 'delete',
        'SYNC': 'sync',           # 同步權限
        'IMPORT': 'import',       # 導入權限
        'EXPORT': 'export',       # 導出權限
        'APPROVE': 'approve',     # 審批權限
    }
})
```

**權限示例：**
```python
# 轉貨單權限
'to.view_to'        # 轉貨單查看
'to.add_to'         # 轉貨單添加
'to.change_to'      # 轉貨單修改
'to.delete_to'      # 轉貨單刪除
'to.sync_to'        # 轉貨單同步
'to.import_to'      # 轉貨單導入
'to.export_to'      # 轉貨單導出

# 銷售發票權限
'sales_invoice.view_sales_invoice'
'sales_invoice.add_sales_invoice'
'sales_invoice.change_sales_invoice'
'sales_invoice.approve_sales_invoice'

# 系統級權限
'view_taicheng_system'    # 系統查看權限
'manage_taicheng_system'  # 系統管理權限
```

**視圖使用示例：**
```python
# 轉貨單列表視圖
class TransferOrderListView(ModulePermissionRequiredMixin, ListView):
    required_module = 'TAICHENG'
    required_permissions = ['to.view_to']

# 轉貨單導入視圖
class TransferOrderImportView(ModulePermissionRequiredMixin, FormView):
    required_module = 'TAICHENG'
    required_permissions = ['to.import_to', 'to.add_to']

# 銷售發票審批視圖
class SalesInvoiceApprovalView(ModulePermissionRequiredMixin, UpdateView):
    required_module = 'TAICHENG'
    required_permissions = ['sales_invoice.approve_sales_invoice']
```

---

### 2. 庫存系統 (STS - Stock Taking System)

**系統描述：** 庫存管理系統，處理庫存盤點、借出管理、付款處理等。

```python
# settings.py
configure_sso_settings(globals(), {
    'SSO_SERVER_URL': 'http://sso.lungfung.hk',
    'MODULE_CODE': 'STS',
    'VERIFY_SSL': True,
    'REQUEST_TIMEOUT': 5,
    'CHILD_MODULES': {
        'INVENTORY': 'inventory',     # 庫存管理
        'LENDING': 'lending',         # 借出管理
        'PAYMENT': 'payment',         # 付款管理
        'COMPANY': 'company',         # 公司管理
        'LOCATION': 'location',       # 地點管理
        'LOGISTICS': 'logistics',     # 物流管理
        'STOCKTAKING': 'stocktaking', # 盤點管理
        'ADJUSTMENT': 'adjustment',   # 庫存調整
    },
    'PARENT_PERMISSIONS': {
        'VIEW_SYSTEM': 'view_inventory_system',
        'MANAGE_SYSTEM': 'manage_inventory_system',
    },
    'CHILD_PERMISSION_TYPES': {
        'VIEW': 'view',
        'ADD': 'add',
        'CHANGE': 'change',
        'DELETE': 'delete',
        'PROCESS': 'process',     # 處理權限
        'CONFIRM': 'confirm',     # 確認權限
        'CANCEL': 'cancel',       # 取消權限
    }
})
```

**權限示例：**
```python
# 庫存管理權限
'inventory.view_inventory'
'inventory.add_inventory'
'inventory.change_inventory'
'inventory.process_inventory'

# 借出管理權限
'lending.view_lending'
'lending.add_lending'
'lending.confirm_lending'
'lending.cancel_lending'

# 盤點管理權限
'stocktaking.view_stocktaking'
'stocktaking.add_stocktaking'
'stocktaking.process_stocktaking'

# 系統級權限
'view_inventory_system'
'manage_inventory_system'
```

**視圖使用示例：**
```python
# 庫存列表視圖
class InventoryListView(ModulePermissionRequiredMixin, ListView):
    required_module = 'STS'
    required_permissions = ['inventory.view_inventory']

# 借出處理視圖
class LendingProcessView(ModulePermissionRequiredMixin, UpdateView):
    required_module = 'STS'
    required_permissions = ['lending.process_lending']

# 盤點確認視圖
class StocktakingConfirmView(ModulePermissionRequiredMixin, View):
    required_module = 'STS'
    required_permissions = ['stocktaking.confirm_stocktaking']
```

---

### 3. 會計系統 (ACS - Accounting System)

**系統描述：** 財務會計系統，處理總賬、應收應付、固定資產等財務業務。

```python
# settings.py
configure_sso_settings(globals(), {
    'SSO_SERVER_URL': 'http://sso.lungfung.hk',
    'MODULE_CODE': 'ACS',
    'VERIFY_SSL': True,
    'REQUEST_TIMEOUT': 5,
    'CHILD_MODULES': {
        'GENERAL_LEDGER': 'gl',       # 總賬
        'ACCOUNTS_PAYABLE': 'ap',     # 應付賬款
        'ACCOUNTS_RECEIVABLE': 'ar',  # 應收賬款
        'FIXED_ASSETS': 'fa',         # 固定資產
        'REPORTS': 'reports',         # 財務報表
        'BUDGET': 'budget',           # 預算管理
        'CASHFLOW': 'cashflow',       # 現金流管理
        'JOURNAL': 'journal',         # 日記帳
    },
    'PARENT_PERMISSIONS': {
        'VIEW_SYSTEM': 'view_accounting_system',
        'MANAGE_SYSTEM': 'manage_accounting_system',
    },
    'CHILD_PERMISSION_TYPES': {
        'VIEW': 'view',
        'ADD': 'add',
        'CHANGE': 'change',
        'DELETE': 'delete',
        'POST': 'post',           # 過帳權限
        'CLOSE': 'close',         # 結帳權限
        'REVERSE': 'reverse',     # 沖銷權限
        'APPROVE': 'approve',     # 審批權限
    }
})
```

**權限示例：**
```python
# 總賬權限
'gl.view_gl'
'gl.add_gl'
'gl.post_gl'
'gl.close_gl'

# 應付賬款權限
'ap.view_ap'
'ap.add_ap'
'ap.approve_ap'
'ap.reverse_ap'

# 財務報表權限
'reports.view_reports'
'reports.add_reports'

# 系統級權限
'view_accounting_system'
'manage_accounting_system'
```

**視圖使用示例：**
```python
# 總賬查詢視圖
class GeneralLedgerView(ModulePermissionRequiredMixin, ListView):
    required_module = 'ACS'
    required_permissions = ['gl.view_gl']

# 應付賬款審批視圖
class AccountsPayableApprovalView(ModulePermissionRequiredMixin, UpdateView):
    required_module = 'ACS'
    required_permissions = ['ap.approve_ap']

# 財務報表視圖
class FinancialReportsView(ModulePermissionRequiredMixin, TemplateView):
    required_module = 'ACS'
    required_permissions = ['reports.view_reports']
```

---

### 4. 人力資源系統 (HRS - Human Resource System)

**系統描述：** 人力資源管理系統，處理員工信息、薪資、考勤、培訓等。

```python
# settings.py
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
        'RECRUITMENT': 'recruitment', # 招聘管理
        'BENEFITS': 'benefits',       # 福利管理
    },
    'PARENT_PERMISSIONS': {
        'VIEW_SYSTEM': 'view_hr_system',
        'MANAGE_SYSTEM': 'manage_hr_system',
    },
    'CHILD_PERMISSION_TYPES': {
        'VIEW': 'view',
        'ADD': 'add',
        'CHANGE': 'change',
        'DELETE': 'delete',
        'APPROVE': 'approve',     # 審批權限
        'PROCESS': 'process',     # 處理權限
        'CALCULATE': 'calculate', # 計算權限
        'REPORT': 'report',       # 報表權限
    }
})
```

**權限示例：**
```python
# 員工管理權限
'employee.view_employee'
'employee.add_employee'
'employee.change_employee'

# 薪資管理權限
'payroll.view_payroll'
'payroll.calculate_payroll'
'payroll.process_payroll'

# 請假管理權限
'leave.view_leave'
'leave.add_leave'
'leave.approve_leave'

# 績效管理權限
'performance.view_performance'
'performance.add_performance'
'performance.report_performance'

# 系統級權限
'view_hr_system'
'manage_hr_system'
```

**視圖使用示例：**
```python
# 員工列表視圖
class EmployeeListView(ModulePermissionRequiredMixin, ListView):
    required_module = 'HRS'
    required_permissions = ['employee.view_employee']

# 薪資計算視圖
class PayrollCalculationView(ModulePermissionRequiredMixin, FormView):
    required_module = 'HRS'
    required_permissions = ['payroll.calculate_payroll']

# 請假審批視圖
class LeaveApprovalView(ModulePermissionRequiredMixin, UpdateView):
    required_module = 'HRS'
    required_permissions = ['leave.approve_leave']
```

---

### 5. 銷售系統 (SLS - Sales System)

**系統描述：** 銷售管理系統，處理客戶管理、訂單處理、銷售報表等。

```python
# settings.py
configure_sso_settings(globals(), {
    'SSO_SERVER_URL': 'http://sso.lungfung.hk',
    'MODULE_CODE': 'SLS',
    'VERIFY_SSL': True,
    'REQUEST_TIMEOUT': 5,
    'CHILD_MODULES': {
        'CUSTOMER': 'customer',       # 客戶管理
        'ORDER': 'order',             # 訂單管理
        'QUOTATION': 'quotation',     # 報價管理
        'DELIVERY': 'delivery',       # 交貨管理
        'INVOICE': 'invoice',         # 發票管理
        'COMMISSION': 'commission',   # 佣金管理
        'TERRITORY': 'territory',     # 銷售區域
        'CAMPAIGN': 'campaign',       # 營銷活動
    },
    'PARENT_PERMISSIONS': {
        'VIEW_SYSTEM': 'view_sales_system',
        'MANAGE_SYSTEM': 'manage_sales_system',
    },
    'CHILD_PERMISSION_TYPES': {
        'VIEW': 'view',
        'ADD': 'add',
        'CHANGE': 'change',
        'DELETE': 'delete',
        'APPROVE': 'approve',
        'SHIP': 'ship',
        'INVOICE': 'invoice',
        'CALCULATE': 'calculate',
    }
})
```

---

### 6. 採購系統 (PCS - Purchasing System)

**系統描述：** 採購管理系統，處理供應商管理、採購訂單、收貨等業務。

```python
# settings.py
configure_sso_settings(globals(), {
    'SSO_SERVER_URL': 'http://sso.lungfung.hk',
    'MODULE_CODE': 'PCS',
    'VERIFY_SSL': True,
    'REQUEST_TIMEOUT': 5,
    'CHILD_MODULES': {
        'VENDOR': 'vendor',           # 供應商管理
        'PURCHASE_ORDER': 'po',       # 採購訂單
        'REQUISITION': 'requisition', # 採購申請
        'RECEIPT': 'receipt',         # 收貨管理
        'QUALITY': 'quality',         # 質量檢驗
        'CONTRACT': 'contract',       # 合同管理
        'EVALUATION': 'evaluation',   # 供應商評估
    },
    'PARENT_PERMISSIONS': {
        'VIEW_SYSTEM': 'view_purchasing_system',
        'MANAGE_SYSTEM': 'manage_purchasing_system',
    },
    'CHILD_PERMISSION_TYPES': {
        'VIEW': 'view',
        'ADD': 'add',
        'CHANGE': 'change',
        'DELETE': 'delete',
        'APPROVE': 'approve',
        'RECEIVE': 'receive',
        'INSPECT': 'inspect',
        'CLOSE': 'close',
    }
})
```

## 🔧 權限配置最佳實踐

### 1. 權限分層設計

```
系統級權限
├── manage_system_system (完整管理權限)
├── view_system_system (系統查看權限)
└── 模組級權限
    ├── module.view_module
    ├── module.add_module
    ├── module.change_module
    ├── module.delete_module
    └── module.special_action_module (特殊權限)
```

### 2. 角色權限建議

#### 系統管理員
```python
required_permissions = ['manage_system_name_system']
```

#### 部門經理
```python
required_permissions = ['view_system_name_system']
```

#### 操作員
```python
required_permissions = [
    'module1.view_module1',
    'module1.add_module1',
    'module2.view_module2'
]
```

#### 審計員
```python
required_permissions = [
    'module1.view_module1',
    'module2.view_module2',
    'reports.view_reports'
]
```

### 3. 自定義權限類型

根據業務需求添加特殊權限：

```python
'CHILD_PERMISSION_TYPES': {
    # 標準權限
    'VIEW': 'view',
    'ADD': 'add',
    'CHANGE': 'change',
    'DELETE': 'delete',
    
    # 業務特殊權限
    'APPROVE': 'approve',     # 審批
    'REJECT': 'reject',       # 拒絕
    'CLOSE': 'close',         # 關閉
    'REOPEN': 'reopen',       # 重新開啟
    'EXPORT': 'export',       # 導出
    'IMPORT': 'import',       # 導入
    'SYNC': 'sync',           # 同步
    'CALCULATE': 'calculate', # 計算
    'PROCESS': 'process',     # 處理
    'CONFIRM': 'confirm',     # 確認
    'CANCEL': 'cancel',       # 取消
}
```

## 📊 權限矩陣示例

| 角色 | 系統查看 | 系統管理 | 添加記錄 | 修改記錄 | 刪除記錄 | 審批 | 報表 |
|------|----------|----------|----------|----------|----------|------|------|
| 系統管理員 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 部門經理 | ✅ | ❌ | ✅ | ✅ | ❌ | ✅ | ✅ |
| 高級操作員 | ✅ | ❌ | ✅ | ✅ | ❌ | ❌ | ✅ |
| 普通操作員 | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| 審計員 | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| 訪客 | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |

## 🎯 系統間權限繼承

某些權限可以在系統間共享：

```python
# 跨系統權限檢查示例
def dashboard_view(request):
    context = {
        # 台城系統權限
        'can_view_taicheng': check_permission(request.user, 'TAICHENG', ['view_taicheng_system']),
        
        # 庫存系統權限
        'can_view_inventory': check_permission(request.user, 'STS', ['view_inventory_system']),
        
        # 會計系統權限
        'can_view_accounting': check_permission(request.user, 'ACS', ['view_accounting_system']),
        
        # HR 系統權限
        'can_view_hr': check_permission(request.user, 'HRS', ['view_hr_system']),
    }
    return render(request, 'dashboard.html', context)
```

這個配置系統確保了：
1. ✅ **統一性** - 所有系統使用相同的權限檢查機制
2. ✅ **靈活性** - 每個系統可以定義自己的模組和權限
3. ✅ **可擴展性** - 易於添加新的系統和權限
4. ✅ **安全性** - 細粒度的權限控制
5. ✅ **可維護性** - 集中的權限管理

---

*本文檔會根據新系統的加入和業務需求的變化持續更新。*
