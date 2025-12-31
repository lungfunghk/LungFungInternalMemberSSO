import logging
import json
from django.conf import settings

logger = logging.getLogger(__name__)

class User:
    """
    統一的用戶類
    
    代表已認證的用戶，包含用戶屬性和權限信息。
    用於在中間件和認證後端之間共享用戶數據。
    
    屬性:
        id (int): 用戶ID
        username (str): 用戶名
        email (str): 電子郵件
        first_name (str): 名
        last_name (str): 姓
        is_active (bool): 用戶狀態
        is_staff (bool): 是否為工作人員
        is_superuser (bool): 是否為超級用戶
        modules (list): 用戶有權訪問的模塊列表
        permissions (dict): 用戶權限數據
        token (str): 用戶令牌
    """
    
    def __init__(self, user_data):
        """
        初始化用戶對象
        
        參數:
            user_data (dict): 用戶數據字典，通常來自 SSO 服務的響應
        """
        
        # 保存原始用戶數據，用於訪問完整的 profile 信息
        self._user_data = user_data
        
        # 如果有 profile 數據，提取其中的字段
        # 注意：profile 可能是 None，需要處理
        profile_data = user_data.get('profile') or {}
        
        self.id = user_data.get('id')
        self.pk = self.id  # Django 兼容性 - pk 是 id 的別名
        self.username = user_data.get('username', '')
        
        # 優先從頂層獲取，如果沒有則從 profile 中獲取
        self.email = user_data.get('email') or profile_data.get('email', '')
        self.first_name = user_data.get('first_name') or profile_data.get('first_name', '')
        self.last_name = user_data.get('last_name') or profile_data.get('last_name', '')
        self.is_active = user_data.get('is_active', True)
        self.is_staff = user_data.get('is_staff', False)
        self.is_superuser = user_data.get('is_superuser', False)
        self.modules = user_data.get('modules', [])
        self.permissions = user_data.get('permissions', {})
        self.token = user_data.get('token', '')
        
        # 添加額外的用戶資料屬性 - 從頂層或 profile 中獲取
        self.display_name = (
            user_data.get('display_name') or 
            profile_data.get('full_name') or 
            self.get_full_name()
        )
        self.avatar_url = user_data.get('avatar_url') or profile_data.get('avatar_url', '')
        self.department = user_data.get('department') or profile_data.get('department', '')
        self.position = user_data.get('position') or profile_data.get('position', '')
        
        # 從 profile 中獲取員工編號和其他資料
        self.staff_no = profile_data.get('staff_number', '')
        self.staff_number = self.staff_no  # 別名
        self.phone_number = profile_data.get('phone_number', '')
        self.full_name = profile_data.get('full_name', self.get_full_name())
        
        # 保存 profile 數據方便訪問
        self.profile = profile_data
        
        # 添加經過驗證的標誌，所有使用此類生成的用戶都被視為已認證
        self.is_authenticated = True
        
        # 獲取日誌級別
        log_level = getattr(settings, 'SSO_LOGGING_LEVEL', 'DEBUG' if settings.DEBUG else 'INFO')
        if log_level == 'DEBUG':
            logger.debug(f"用戶對象已建立: {self.username}")
        
    def has_perm(self, perm, obj=None):
        """
        檢查用戶是否具有指定權限
        
        參數:
            perm (str): 權限編碼，格式為 'module_code.permission_code'
            obj (object, optional): 權限相關的對象，當前未使用
            
        返回:
            bool: 是否具有權限
        """
        # 超級用戶有所有權限
        if self.is_superuser:
            logger.debug(f"超級用戶 {self.username} 自動獲得權限 {perm}")
            return True
            
        # 權限格式為 'module_code.permission_code'
        try:
            module_code, perm_code = perm.split('.')
        except ValueError:
            logger.warning(f"權限格式無效: {perm}")
            return False
            
        # 檢查模塊權限
        module_permissions = self.permissions.get(module_code, {})
        if perm_code in module_permissions.get('permissions', []):
            logger.debug(f"用戶 {self.username} 具有權限 {perm}")
            return True
            
        logger.debug(f"用戶 {self.username} 沒有權限 {perm}")
        return False
        
    def has_module_perms(self, module_code):
        """
        檢查用戶是否有權訪問指定模塊
        
        參數:
            module_code (str): 模塊編碼
            
        返回:
            bool: 是否有權訪問模塊
        """
        # 超級用戶可訪問所有模塊
        if self.is_superuser:
            logger.debug(f"超級用戶 {self.username} 自動獲得模塊 {module_code} 的訪問權限")
            return True
            
        # 檢查模塊訪問權限
        has_access = module_code in self.modules
        
        if has_access:
            logger.debug(f"用戶 {self.username} 有權訪問模塊 {module_code}")
        else:
            logger.debug(f"用戶 {self.username} 無權訪問模塊 {module_code}")
            
        return has_access
        
    def get_all_permissions(self):
        """
        獲取用戶的所有權限
        
        返回:
            dict: 用戶權限數據
        """
        return self.permissions
        
    def set_permissions(self, permissions_data):
        """
        設置用戶權限數據
        
        參數:
            permissions_data (dict): 權限數據
            
        返回:
            None
        """
        try:
            if permissions_data and isinstance(permissions_data, dict):
                self.permissions = permissions_data
                # 從權限數據中提取模塊列表
                self.modules = list(permissions_data.keys())
                logger.debug(f"用戶 {self.username} 的權限數據已設置，模塊: {self.modules}")
            else:
                logger.warning(f"無效的權限數據: {json.dumps(permissions_data)}")
        except Exception as e:
            logger.error(f"設置權限數據時發生錯誤: {str(e)}", exc_info=True)
    
    def get_full_name(self):
        """
        獲取用戶全名
        
        返回:
            str: 用戶全名
        """
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        else:
            return self.username
    
    def get_profile(self):
        """
        獲取用戶個人資料
        
        返回:
            dict: 用戶個人資料數據
        """
        profile = {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.get_full_name(),
            'display_name': self.display_name,
            'is_active': self.is_active,
            'is_staff': self.is_staff,
            'is_superuser': self.is_superuser
        }
        
        # 添加可能存在的額外屬性
        if hasattr(self, 'avatar_url') and self.avatar_url:
            profile['avatar_url'] = self.avatar_url
        
        if hasattr(self, 'department') and self.department:
            profile['department'] = self.department
            
        if hasattr(self, 'position') and self.position:
            profile['position'] = self.position
            
        return profile
        
    def __str__(self):
        """
        返回用戶的字符串表示
        """
        return f"User: {self.username} ({self.email})" 