# lungfung_sso/permissions.py
from rest_framework.permissions import BasePermission
from django.conf import settings
import requests
from functools import wraps
import logging
from enum import Enum
import json
from django.contrib import messages
from django.http import HttpResponseForbidden
from .exceptions import PermissionDeniedError
from .cache import get_user_permissions_cache, set_user_permissions_cache
from django.shortcuts import render

logger = logging.getLogger(__name__)

class ModulePermissionRequiredMixin:
    """
    權限檢查 Mixin，用於基於類的視圖
    
    使用方法：
    class MyView(ModulePermissionRequiredMixin, ListView):
        required_module = 'TAICHENG'  # 模組名稱
        required_permissions = ['view_sales_invoice']  # 所需權限列表
    """
    required_module = None
    required_permissions = []
    
    def dispatch(self, request, *args, **kwargs):
        """重寫 dispatch 方法來檢查權限"""
        if not self.check_permissions(request):
            error = PermissionDeniedError('您沒有訪問此頁面的權限')
            return render(request, 'portal/403.html', {'error': error.message}, status=403)
        return super().dispatch(request, *args, **kwargs)
    
    def check_permissions(self, request):
        """檢查用戶權限"""
        if not request.user or not request.user.is_authenticated:
            return False
            
        # 如果是超級用戶，直接允許訪問
        if hasattr(request.user, 'is_superuser') and request.user.is_superuser:
            return True
            
        if not self.required_permissions:
            return True
            
        return check_permission(request.user, self.required_module, self.required_permissions)

# 從設置中獲取模組配置
class Module(str, Enum):
    """模組枚舉 - 動態從設置加載"""
    
    @classmethod
    def get_parent_module(cls):
        """獲取父模組名稱"""
        return getattr(settings, 'SSO_MODULES', {}).get('PARENT_MODULE', 'DEFAULT')
    
    @classmethod
    def get_child_modules(cls):
        """獲取所有子模組"""
        child_modules = getattr(settings, 'SSO_MODULES', {}).get('CHILD_MODULES', {})
        return list(child_modules.values())
    
    @classmethod
    def get_child_module_mapping(cls):
        """獲取子模組名稱到代碼的映射"""
        return getattr(settings, 'SSO_MODULES', {}).get('CHILD_MODULES', {})

# 從設置中獲取權限配置
class Permission(Enum):
    """權限枚舉 - 動態從設置加載"""
    
    @classmethod
    def get_parent_permissions(cls):
        """獲取父模組權限"""
        return getattr(settings, 'SSO_PERMISSIONS', {}).get('PARENT_PERMISSIONS', {
            'VIEW_SYSTEM': 'view_default_system',
            'MANAGE_SYSTEM': 'manage_default_system',
        })
    
    @classmethod
    def get_child_permission_types(cls):
        """獲取子模組權限類型"""
        return getattr(settings, 'SSO_PERMISSIONS', {}).get('CHILD_PERMISSION_TYPES', {
            'VIEW': 'view',
            'ADD': 'add',
            'CHANGE': 'change',
            'DELETE': 'delete',
        })

    @classmethod
    def format_permission(cls, module: str, action: str) -> str:
        """格式化權限字符串"""
        parent_module = Module.get_parent_module()
        
        # 父模組權限直接返回 action 值本身
        if module == parent_module:
            return action
        
        # 檢查 action 是否已經包含模組信息
        # 如果 action 已經是完整格式（如 'delete_tc_customer'），直接使用
        # 如果 action 是基本類型（如 'delete'），則需要添加模組信息
        if action.endswith(f'_{module}') or f'_{module}_' in action:
            # action 已經包含模組信息，直接使用 module.action 格式
            return f"{module}.{action}"
        else:
            # action 是基本類型，需要構造完整的權限名稱
            return f"{module}.{action}_{module}"

class SSOPermission(BasePermission):
    """SSO權限檢查類"""
    
    def _get_user_permissions(self, request):
        """獲取用戶權限數據"""
        if not hasattr(request.user, 'id') or not request.user.id:
            logger.warning("用戶對象缺少 id 屬性，無法獲取權限")
            return None
            
        logger.info(f"開始獲取用戶 {request.user.username} (ID: {request.user.id}) 的權限數據")
        
        # 使用緩存函數獲取權限數據
        permissions_data = get_user_permissions_cache(request.user.id)
        
        if permissions_data:
            logger.info(f"從緩存中獲取到用戶權限數據")
            return permissions_data
        
        try:
            # 改進的 token 獲取邏輯 - 優先從 user.token 獲取
            auth_token = None
            
            # 優先級1：從用戶對象的 token 屬性獲取
            if hasattr(request.user, 'token') and request.user.token:
                auth_token = request.user.token
                logger.debug("從用戶對象的 token 屬性獲取認證令牌")
            # 優先級2：從 Authorization header 獲取
            elif request.headers.get('Authorization'):
                auth_header = request.headers.get('Authorization')
                if auth_header.startswith('Bearer '):
                    auth_token = auth_header.split(' ')[1]
                else:
                    auth_token = auth_header
                logger.debug("從 Authorization header 獲取認證令牌")
            # 優先級3：從 cookies 獲取
            elif 'auth_access_token' in request.COOKIES:
                auth_token = request.COOKIES.get('auth_access_token')
                logger.debug("從 cookies 獲取認證令牌")
            
            # 如果沒有找到 token，記錄錯誤並返回 None
            if not auth_token:
                logger.error("無法獲取認證令牌：用戶對象無 token 屬性，請求頭無 Authorization，cookies 無 auth_access_token")
                return None
            
            # 構造請求參數
            permissions_url = f"{settings.SSO_SERVICE['URL']}{settings.SSO_SERVICE['USER_PERMISSIONS_URL']}"
            headers = {'Authorization': f'Bearer {auth_token}'}
            params = {'user_id': request.user.id}  # 添加 user_id 參數
            timeout = getattr(settings, 'SSO_REQUEST_TIMEOUT', 5)
            
            logger.info(f"從 SSO 服務獲取權限數據，URL: {permissions_url}, User ID: {request.user.id}")
            logger.debug(f"使用認證令牌: {auth_token[:10]}...{auth_token[-4:] if len(auth_token) > 14 else auth_token}")
            
            response = requests.get(
                permissions_url,
                params=params,
                headers=headers,
                verify=settings.SSO_SERVICE['VERIFY_SSL'],
                timeout=timeout
            )
            
            logger.debug(f"SSO 響應狀態碼: {response.status_code}")
            logger.debug(f"SSO 響應內容: {response.text}")
            
            if response.status_code == 200:
                permissions_data = response.json()
                logger.info(f"成功獲取權限數據")
                
                # 使用緩存函數設置權限數據
                cache_timeout = getattr(settings, 'USER_CACHE_TIMEOUT', 300)
                set_user_permissions_cache(request.user.id, permissions_data, cache_timeout)
                logger.debug(f"權限數據已存入緩存，過期時間: {cache_timeout}秒")
                
                return permissions_data
            else:
                logger.error(f"從 SSO 獲取權限失敗: HTTP {response.status_code}, 響應: {response.text}")
                return None
        except Exception as e:
            logger.error(f"獲取權限時發生錯誤: {str(e)}", exc_info=True)
            return None
        
    def _get_parent_module_permissions(self, permissions_data):
        """獲取父模組權限"""
        logger.debug("開始獲取父模組權限")
        parent_permissions = set()
        
        # 獲取父模組編碼
        parent_module = Module.get_parent_module()
        
        for module_data in permissions_data.get('permissions', []):
            if module_data['code'] == parent_module:
                parent_permissions = {perm['codename'] for perm in module_data.get('permissions', [])}
                logger.info(f"找到父模組權限: {parent_permissions}")
                break
                
        if not parent_permissions:
            logger.warning("未找到父模組權限")
            
        return parent_permissions
        
    def _collect_module_permissions(self, permissions_data):
        """收集所有權限"""
        logger.info("開始收集所有模組權限")
        all_permissions = set()
        
        # 獲取父模組權限
        parent_permissions = self._get_parent_module_permissions(permissions_data)
        logger.debug(f"父模組權限: {parent_permissions}")
        
        # 將父模組權限添加到所有權限集合中
        all_permissions.update(parent_permissions)
        logger.debug(f"添加父模組權限到權限集合: {parent_permissions}")
        
        # 獲取父模組權限的值
        parent_perms = Permission.get_parent_permissions()
        
        # 檢查父模組特殊權限
        has_manage_system = parent_perms.get('MANAGE_SYSTEM', 'manage_default_system') in parent_permissions
        has_view_system = parent_perms.get('VIEW_SYSTEM', 'view_default_system') in parent_permissions
        
        logger.debug(f"系統管理權限: {has_manage_system}, 系統查看權限: {has_view_system}")
        
        # 如果有系統管理權限,添加所有子模組的所有權限
        if has_manage_system:
            logger.info("用戶具有系統管理權限，添加所有子模組權限")
            for module in Module.get_child_modules():
                for perm_type in Permission.get_child_permission_types().values():
                    permission = Permission.format_permission(module, perm_type)
                    all_permissions.add(permission)
                    logger.debug(f"添加權限: {permission}")
            return all_permissions
            
        # 如果有系統查看權限,添加所有子模組的查看權限
        if has_view_system:
            logger.info("用戶具有系統查看權限，添加所有子模組的查看權限")
            view_perm = Permission.get_child_permission_types().get('VIEW', 'view')
            logger.info(f"添加所有子模組的查看權限: {view_perm}")
            for module in Module.get_child_modules():
                permission = Permission.format_permission(module, view_perm)
                all_permissions.add(permission)
                logger.debug(f"添加查看權限: {permission}")
        
        # 處理子模組權限
        logger.info("處理子模組具體權限")
        parent_module = Module.get_parent_module()
        for module_data in permissions_data.get('permissions', []):
            module_code = module_data['code']
            if module_code == parent_module:
                continue
                
            # 添加子模組的具體權限
            for perm in module_data.get('permissions', []):
                perm_code = f"{module_code}.{perm['codename']}"
                all_permissions.add(perm_code)
                logger.debug(f"添加子模組權限: {perm_code}")
        
        logger.info(f"收集到的所有權限: {all_permissions}")
        return all_permissions
        
    def has_permission(self, request, view):
        """檢查權限"""
        logger.info(f"開始檢查用戶 {request.user.username if request.user else 'AnonymousUser'} 的權限")
        
        if not request.user or not request.user.is_authenticated:
            logger.warning("用戶未認證")
            return False
            
        # 如果是超級用戶,直接允許訪問
        if hasattr(request.user, 'is_superuser') and request.user.is_superuser:
            logger.info("超級用戶，允許訪問")
            return True
            
        # 獲取視圖所需權限
        required_permissions = getattr(view, 'required_permissions', [])
        if not required_permissions:
            logger.info("視圖未要求特定權限，允許訪問")
            return True
            
        logger.info(f"視圖要求的權限: {required_permissions}")
        
        # 獲取權限數據
        permissions_data = self._get_user_permissions(request)
        if not permissions_data:
            logger.error(f"無法獲取用戶 {request.user.username} 的權限數據")
            return False
            
        # 收集所有權限並檢查
        all_permissions = self._collect_module_permissions(permissions_data)
        has_all_permissions = all(perm in all_permissions for perm in required_permissions)
        
        logger.info(f"權限檢查結果: {has_all_permissions} (用戶: {request.user.username}, 要求權限: {required_permissions})")
        return has_all_permissions

class SSOperationPermission:
    """SSO操作權限檢查類 - 用於函數裝飾器"""
    
    @staticmethod
    def _get_user_permissions(request):
        """獲取用戶權限數據"""
        return SSOPermission()._get_user_permissions(request)
    
    @staticmethod
    def _collect_module_permissions(permissions_data):
        """收集所有權限"""
        return SSOPermission()._collect_module_permissions(permissions_data)

def check_permission(user, module, permissions):
    """
    檢查用戶是否具有指定模組的權限
    
    Args:
        user: Django 用戶對象
        module: 模組名稱
        permissions: 權限列表（可以是字符串或列表）
        
    Returns:
        bool: 是否具有權限
    """
    if not user or not user.is_authenticated:
        return False
        
    # 如果是超級用戶,直接允許訪問
    if hasattr(user, 'is_superuser') and user.is_superuser:
        return True
    
    # 轉換為列表
    if isinstance(permissions, str):
        permissions = [permissions]
    
    try:
        # 優先從緩存獲取權限數據，避免依賴 MockRequest
        permissions_data = get_user_permissions_cache(user.id)
        
        # 如果緩存中沒有權限數據，嘗試使用帶認證信息的模擬請求
        if not permissions_data:
            logger.debug(f"用戶 {user.username} (ID: {user.id}) 沒有緩存的權限數據，嘗試使用模擬請求")
            
            # 改進的模擬請求對象，包含真實的認證信息
            class MockRequest:
                def __init__(self, user):
                    self.user = user
                    self.headers = {}
                    self.COOKIES = {}
                    
                    # 如果用戶對象有 token，添加到模擬的 cookies 中
                    if hasattr(user, 'token') and user.token:
                        self.COOKIES['auth_access_token'] = user.token
                        logger.debug("模擬請求：從用戶對象添加 token 到 cookies")
            
            mock_request = MockRequest(user)
            permissions_data = SSOPermission()._get_user_permissions(mock_request)
            
            if not permissions_data:
                logger.warning(f"無法獲取用戶 {user.username} (ID: {user.id}) 的權限數據")
                return False
        
        # 收集所有權限
        all_permissions = SSOPermission()._collect_module_permissions(permissions_data)
        logger.debug(f"用戶 {user.username} 的所有權限: {sorted(list(all_permissions))}")
        
        # 檢查具體權限
        for perm in permissions:
            # 格式化權限
            formatted_perm = Permission.format_permission(module, perm)
            logger.debug(f"檢查權限: {formatted_perm}")
            if formatted_perm not in all_permissions:
                logger.warning(f"用戶 {user.username} 缺少權限: {formatted_perm}")
                return False
                
        logger.info(f"用戶 {user.username} 權限檢查通過")
        return True
    except Exception as e:
        logger.error(f"檢查權限時發生錯誤: {str(e)}", exc_info=True)
        return False

def module_permission_required(*permissions):
    """權限裝飾器"""
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(viewset, request, *args, **kwargs):
            logger.info(f"檢查用戶 {request.user.username} 的模組權限")
            
            # 檢查是否為超級用戶
            if hasattr(request.user, 'is_superuser') and request.user.is_superuser:
                logger.info(f"用戶 {request.user.username} 是超級用戶，允許訪問")
                return view_func(viewset, request, *args, **kwargs)
            
            # 獲取權限數據
            permissions_data = SSOPermission()._get_user_permissions(request)
            if not permissions_data:
                logger.error(f"無法獲取用戶 {request.user.username} 的權限數據")
                
                # 使用 PermissionDeniedError
                error = PermissionDeniedError('無法獲取權限數據')
                return render(request, 'portal/403.html', {'error': error.message}, status=403)
                
            # 收集所有權限
            all_permissions = SSOPermission()._collect_module_permissions(permissions_data)
            logger.debug(f"用戶 {request.user.username} 的所有權限: {all_permissions}")
            
            # 檢查具體權限
            parent_module = Module.get_parent_module()
            for perm in permissions:
                # 轉換權限格式
                if isinstance(perm, tuple) and len(perm) == 2:
                    module, action = perm
                    if module == parent_module:
                        # 父模組權限直接使用 action 值
                        perm = action if isinstance(action, str) else action.value
                    else:
                        # 子模組權限使用格式化方法
                        perm = Permission.format_permission(module, action)
                
                if perm not in all_permissions:
                    logger.warning(f"用戶 {request.user.username} 缺少權限: {perm}")
                    
                    # 使用 PermissionDeniedError
                    error = PermissionDeniedError(f'缺少所需權限: {perm}')
                    return render(request, 'portal/403.html', {'error': error.message}, status=403)
                    
            logger.info(f"用戶 {request.user.username} 通過權限檢查")
            return view_func(viewset, request, *args, **kwargs)
        return _wrapped_view
    return decorator