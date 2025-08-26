# LungFung SSO 實際使用案例

本文檔提供 LungFung 各子系統中 SSO 的實際使用案例和代碼示例。

## 🎯 實際業務場景案例

### 1. 台城系統 - 轉貨單管理

#### 場景：轉貨單業務流程
```python
# views.py
from lungfung_sso import ModulePermissionRequiredMixin, module_permission_required, check_permission
from django.views.generic import ListView, CreateView, UpdateView
from django.contrib import messages
from django.shortcuts import redirect

class TransferOrderListView(ModulePermissionRequiredMixin, ListView):
    """轉貨單列表 - 支持不同權限等級的用戶"""
    model = TransferOrder
    template_name = 'transfer_orders/list.html'
    paginate_by = 20
    
    required_module = 'TAICHENG'
    required_permissions = ['to.view_to']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 根據用戶權限顯示不同操作按鈕
        context.update({
            'can_create': check_permission(self.request.user, 'TAICHENG', ['to.add_to']),
            'can_import': check_permission(self.request.user, 'TAICHENG', ['to.import_to']),
            'can_sync': check_permission(self.request.user, 'TAICHENG', ['to.sync_to']),
            'can_export': check_permission(self.request.user, 'TAICHENG', ['to.export_to']),
            'is_manager': check_permission(self.request.user, 'TAICHENG', ['manage_taicheng_system']),
        })
        return context

class TransferOrderCreateView(ModulePermissionRequiredMixin, CreateView):
    """創建轉貨單"""
    model = TransferOrder
    form_class = TransferOrderForm
    template_name = 'transfer_orders/create.html'
    
    required_module = 'TAICHENG'
    required_permissions = ['to.add_to']
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user.username
        messages.success(self.request, '轉貨單創建成功！')
        return super().form_valid(form)

class TransferOrderImportView(ModulePermissionRequiredMixin, FormView):
    """轉貨單批量導入 - 需要導入和添加權限"""
    template_name = 'transfer_orders/import.html'
    form_class = ImportForm
    
    required_module = 'TAICHENG'
    required_permissions = ['to.import_to', 'to.add_to']  # 多個權限
    
    def form_valid(self, form):
        try:
            imported_count = form.process_import(self.request.user)
            messages.success(self.request, f'成功導入 {imported_count} 筆轉貨單')
        except Exception as e:
            messages.error(self.request, f'導入失敗: {str(e)}')
        return redirect('transfer_orders:list')

# 函數視圖示例 - 同步功能
@module_permission_required(('to', 'sync'))
def sync_transfer_orders(request):
    """同步轉貨單到 NAV 系統"""
    if request.method == 'POST':
        try:
            # 同步邏輯
            sync_count = sync_to_nav_system()
            messages.success(request, f'成功同步 {sync_count} 筆轉貨單')
        except Exception as e:
            messages.error(request, f'同步失敗: {str(e)}')
    
    return redirect('transfer_orders:list')
```

#### 模板中的權限控制
```html
<!-- templates/transfer_orders/list.html -->
<div class="toolbar">
    {% if can_create %}
        <a href="{% url 'transfer_orders:create' %}" class="btn btn-primary">
            <i class="fas fa-plus"></i> 新增轉貨單
        </a>
    {% endif %}
    
    {% if can_import %}
        <a href="{% url 'transfer_orders:import' %}" class="btn btn-info">
            <i class="fas fa-upload"></i> 批量導入
        </a>
    {% endif %}
    
    {% if can_sync %}
        <form method="post" action="{% url 'transfer_orders:sync' %}" style="display: inline;">
            {% csrf_token %}
            <button type="submit" class="btn btn-warning" onclick="return confirm('確定要同步嗎？')">
                <i class="fas fa-sync"></i> 同步到 NAV
            </button>
        </form>
    {% endif %}
    
    {% if can_export %}
        <a href="{% url 'transfer_orders:export' %}" class="btn btn-success">
            <i class="fas fa-download"></i> 導出 Excel
        </a>
    {% endif %}
</div>

<!-- 管理員專用功能 -->
{% if is_manager %}
<div class="admin-panel">
    <h4>管理員功能</h4>
    <a href="{% url 'transfer_orders:settings' %}" class="btn btn-secondary">系統設置</a>
    <a href="{% url 'transfer_orders:audit' %}" class="btn btn-secondary">審計日誌</a>
</div>
{% endif %}
```

---

### 2. 庫存系統 - 庫存管理

#### 場景：庫存盤點和調整
```python
# views.py
class InventoryListView(ModulePermissionRequiredMixin, ListView):
    """庫存列表"""
    model = Inventory
    template_name = 'inventory/list.html'
    
    required_module = 'STS'
    required_permissions = ['inventory.view_inventory']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # 根據用戶權限過濾數據
        if not check_permission(self.request.user, 'STS', ['manage_inventory_system']):
            # 非管理員只能查看自己負責的庫存
            queryset = queryset.filter(responsible_person=self.request.user.username)
        
        return queryset

class StocktakingProcessView(ModulePermissionRequiredMixin, UpdateView):
    """庫存盤點處理"""
    model = Stocktaking
    form_class = StocktakingForm
    template_name = 'inventory/stocktaking_process.html'
    
    required_module = 'STS'
    required_permissions = ['stocktaking.process_stocktaking']
    
    def form_valid(self, form):
        # 檢查是否有確認權限
        if form.cleaned_data.get('confirm') and not check_permission(
            self.request.user, 'STS', ['stocktaking.confirm_stocktaking']
        ):
            messages.error(self.request, '您沒有確認盤點的權限')
            return self.form_invalid(form)
        
        return super().form_valid(form)

# 複雜的權限檢查 - 庫存調整
class InventoryAdjustmentView(ModulePermissionRequiredMixin, CreateView):
    """庫存調整"""
    model = InventoryAdjustment
    form_class = AdjustmentForm
    template_name = 'inventory/adjustment.html'
    
    required_module = 'STS'
    required_permissions = ['adjustment.add_adjustment']
    
    def dispatch(self, request, *args, **kwargs):
        # 大額調整需要特殊權限
        amount = request.POST.get('adjustment_amount', 0)
        try:
            amount = float(amount)
            if amount > 10000:  # 大額調整
                if not check_permission(request.user, 'STS', ['adjustment.approve_adjustment']):
                    messages.error(request, '大額庫存調整需要審批權限')
                    return redirect('inventory:list')
        except (ValueError, TypeError):
            pass
        
        return super().dispatch(request, *args, **kwargs)
```

---

### 3. 會計系統 - 財務處理

#### 場景：財務審批流程
```python
# views.py
class AccountsPayableView(ModulePermissionRequiredMixin, ListView):
    """應付賬款管理"""
    model = AccountsPayable
    template_name = 'accounting/ap_list.html'
    
    required_module = 'ACS'
    required_permissions = ['ap.view_ap']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 分別統計不同狀態的賬款
        context.update({
            'pending_approval': self.get_queryset().filter(status='pending').count(),
            'can_approve': check_permission(self.request.user, 'ACS', ['ap.approve_ap']),
            'can_post': check_permission(self.request.user, 'ACS', ['ap.post_ap']),
            'can_reverse': check_permission(self.request.user, 'ACS', ['ap.reverse_ap']),
        })
        return context

class APApprovalView(ModulePermissionRequiredMixin, UpdateView):
    """應付賬款審批"""
    model = AccountsPayable
    form_class = APApprovalForm
    template_name = 'accounting/ap_approval.html'
    
    required_module = 'ACS'
    required_permissions = ['ap.approve_ap']
    
    def get_queryset(self):
        # 只能審批待審核的記錄
        return super().get_queryset().filter(status='pending')

# 複雜的權限組合 - 月結作業
@module_permission_required(('gl', 'close'), ('reports', 'view'))
def month_end_closing(request):
    """月結作業 - 需要多個權限"""
    if request.method == 'POST':
        # 檢查是否為會計主管
        if not check_permission(request.user, 'ACS', ['manage_accounting_system']):
            messages.error(request, '只有會計主管可以執行月結作業')
            return redirect('accounting:dashboard')
        
        try:
            # 執行月結
            result = perform_month_end_closing()
            messages.success(request, f'月結作業完成：{result}')
        except Exception as e:
            messages.error(request, f'月結作業失敗：{str(e)}')
    
    return render(request, 'accounting/month_end.html')
```

---

### 4. 人力資源系統 - 員工管理

#### 場景：員工信息管理和薪資處理
```python
# views.py
class EmployeeDetailView(ModulePermissionRequiredMixin, DetailView):
    """員工詳情"""
    model = Employee
    template_name = 'hr/employee_detail.html'
    
    required_module = 'HRS'
    required_permissions = ['employee.view_employee']
    
    def get_object(self):
        obj = super().get_object()
        
        # 員工只能查看自己的信息，HR 可以查看所有
        if not check_permission(self.request.user, 'HRS', ['manage_hr_system']):
            if obj.username != self.request.user.username:
                raise PermissionDenied('您只能查看自己的員工信息')
        
        return obj
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 根據權限顯示不同信息
        context.update({
            'can_edit': check_permission(self.request.user, 'HRS', ['employee.change_employee']),
            'can_view_salary': check_permission(self.request.user, 'HRS', ['payroll.view_payroll']),
            'can_manage_leave': check_permission(self.request.user, 'HRS', ['leave.approve_leave']),
        })
        return context

class PayrollCalculationView(ModulePermissionRequiredMixin, FormView):
    """薪資計算"""
    template_name = 'hr/payroll_calculation.html'
    form_class = PayrollForm
    
    required_module = 'HRS'
    required_permissions = ['payroll.calculate_payroll']
    
    def form_valid(self, form):
        try:
            # 計算薪資
            results = form.calculate_payroll()
            
            # 檢查是否需要處理權限才能保存
            if form.cleaned_data.get('save_results'):
                if not check_permission(self.request.user, 'HRS', ['payroll.process_payroll']):
                    messages.warning(self.request, '薪資已計算完成，但您沒有處理權限，請聯繫主管確認')
                else:
                    results.save()
                    messages.success(self.request, '薪資計算並保存成功')
            else:
                messages.info(self.request, '薪資計算完成，未保存')
                
        except Exception as e:
            messages.error(self.request, f'薪資計算失敗：{str(e)}')
        
        return super().form_valid(form)

# 請假審批工作流
class LeaveRequestView(ModulePermissionRequiredMixin, CreateView):
    """員工請假申請"""
    model = LeaveRequest
    form_class = LeaveRequestForm
    template_name = 'hr/leave_request.html'
    
    required_module = 'HRS'
    required_permissions = ['leave.add_leave']
    
    def form_valid(self, form):
        form.instance.employee = self.request.user
        form.instance.status = 'pending'
        
        # 自動分配審批人
        if check_permission(self.request.user, 'HRS', ['leave.approve_leave']):
            # 如果申請人本身有審批權限，可能是主管，需要更高級別審批
            form.instance.approver = get_senior_manager()
        else:
            form.instance.approver = get_department_manager(self.request.user)
        
        return super().form_valid(form)

class LeaveApprovalView(ModulePermissionRequiredMixin, UpdateView):
    """請假審批"""
    model = LeaveRequest
    form_class = LeaveApprovalForm
    template_name = 'hr/leave_approval.html'
    
    required_module = 'HRS'
    required_permissions = ['leave.approve_leave']
    
    def get_queryset(self):
        # 只能審批分配給自己的請假申請
        return super().get_queryset().filter(
            approver=self.request.user,
            status='pending'
        )
```

---

### 5. 跨系統權限檢查

#### 場景：統一儀表板
```python
# views.py
class DashboardView(TemplateView):
    """統一儀表板 - 根據用戶權限顯示不同系統的信息"""
    template_name = 'dashboard/main.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # 檢查各系統訪問權限
        system_access = {
            'taicheng': {
                'can_access': check_permission(user, 'TAICHENG', ['view_taicheng_system']),
                'is_admin': check_permission(user, 'TAICHENG', ['manage_taicheng_system']),
                'modules': {}
            },
            'inventory': {
                'can_access': check_permission(user, 'STS', ['view_inventory_system']),
                'is_admin': check_permission(user, 'STS', ['manage_inventory_system']),
                'modules': {}
            },
            'accounting': {
                'can_access': check_permission(user, 'ACS', ['view_accounting_system']),
                'is_admin': check_permission(user, 'ACS', ['manage_accounting_system']),
                'modules': {}
            },
            'hr': {
                'can_access': check_permission(user, 'HRS', ['view_hr_system']),
                'is_admin': check_permission(user, 'HRS', ['manage_hr_system']),
                'modules': {}
            }
        }
        
        # 檢查具體模組權限
        if system_access['taicheng']['can_access']:
            system_access['taicheng']['modules'] = {
                'transfer_orders': check_permission(user, 'TAICHENG', ['to.view_to']),
                'sales_invoices': check_permission(user, 'TAICHENG', ['sales_invoice.view_sales_invoice']),
            }
        
        if system_access['inventory']['can_access']:
            system_access['inventory']['modules'] = {
                'inventory': check_permission(user, 'STS', ['inventory.view_inventory']),
                'lending': check_permission(user, 'STS', ['lending.view_lending']),
                'stocktaking': check_permission(user, 'STS', ['stocktaking.view_stocktaking']),
            }
        
        # 獲取用戶相關的統計數據
        stats = {}
        if system_access['taicheng']['modules'].get('transfer_orders'):
            stats['pending_transfer_orders'] = get_pending_transfer_orders_count(user)
        
        if system_access['hr']['can_access']:
            stats['pending_leave_approvals'] = get_pending_leave_approvals_count(user)
        
        context.update({
            'system_access': system_access,
            'stats': stats,
        })
        
        return context

# 通用權限檢查裝飾器
def system_permission_required(system_code, permissions):
    """通用的系統權限檢查裝飾器"""
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not check_permission(request.user, system_code, permissions):
                messages.error(request, f'您沒有訪問 {system_code} 系統的權限')
                return redirect('dashboard:main')
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

# 使用通用權限檢查
@system_permission_required('TAICHENG', ['to.view_to'])
def transfer_order_api(request):
    """轉貨單 API"""
    data = get_transfer_orders_data(request.user)
    return JsonResponse(data)

@system_permission_required('STS', ['inventory.view_inventory'])
def inventory_api(request):
    """庫存 API"""
    data = get_inventory_data(request.user)
    return JsonResponse(data)
```

---

### 6. 權限異常處理

#### 場景：優雅的權限錯誤處理
```python
# views.py
from lungfung_sso.exceptions import PermissionDeniedError

class BasePermissionView(View):
    """基礎權限視圖 - 統一處理權限錯誤"""
    
    def dispatch(self, request, *args, **kwargs):
        try:
            return super().dispatch(request, *args, **kwargs)
        except PermissionDeniedError as e:
            messages.error(request, f'權限不足：{e.message}')
            return redirect('dashboard:main')
        except Exception as e:
            logger.exception(f'視圖執行錯誤：{str(e)}')
            messages.error(request, '系統錯誤，請聯繫管理員')
            return redirect('dashboard:main')

# 自定義權限檢查中間件
class PermissionLoggingMiddleware:
    """權限檢查日誌中間件"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # 記錄權限檢查
        if hasattr(request, 'user') and request.user.is_authenticated:
            logger.info(f'用戶 {request.user.username} 訪問 {request.path}')
        
        response = self.get_response(request)
        
        # 記錄權限拒絕
        if response.status_code == 403:
            logger.warning(f'用戶 {request.user.username} 訪問 {request.path} 被拒絕')
        
        return response
```

#### 錯誤頁面模板
```html
<!-- templates/403.html -->
<div class="error-page">
    <h1>訪問被拒絕</h1>
    <p>{{ error }}</p>
    
    <div class="suggestions">
        <h3>您可以：</h3>
        <ul>
            <li><a href="{% url 'dashboard:main' %}">返回儀表板</a></li>
            <li>聯繫您的主管申請相關權限</li>
            <li>檢查您是否登錄了正確的賬戶</li>
        </ul>
    </div>
    
    <div class="contact-info">
        <p>如需技術支援，請聯繫 IT 部門：<a href="mailto:it@lungfung.hk">it@lungfung.hk</a></p>
    </div>
</div>
```

## 🎯 最佳實踐總結

### 1. 權限檢查原則
- ✅ 在視圖層進行權限檢查
- ✅ 在模板中根據權限顯示/隱藏功能
- ✅ 在 API 層面也要進行權限驗證
- ✅ 記錄權限檢查日誌以便審計

### 2. 用戶體驗優化
- ✅ 提供清晰的錯誤信息
- ✅ 根據權限動態顯示功能
- ✅ 提供權限申請的指引
- ✅ 優雅地處理權限不足的情況

### 3. 安全考慮
- ✅ 永遠不要僅依賴前端隱藏來控制權限
- ✅ 在後端進行完整的權限驗證
- ✅ 記錄所有權限相關的操作
- ✅ 定期審查和更新權限配置

### 4. 可維護性
- ✅ 使用一致的權限命名規則
- ✅ 集中管理權限配置
- ✅ 提供清晰的權限文檔
- ✅ 建立權限測試機制

這些實際案例展示了 LungFung SSO 在各種業務場景中的靈活應用，確保了系統的安全性和可用性。
