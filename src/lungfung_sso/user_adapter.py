"""
用戶模型適配器
處理SSO用戶和Django用戶模型之間的轉換

當項目中的模型使用 ForeignKey 關聯到 auth.User 時，
需要將 SSO 用戶轉換為 Django 用戶才能正確保存關聯。
"""
import logging
from django.contrib.auth import get_user_model
from django.db import transaction

logger = logging.getLogger(__name__)


class UserAdapter:
    """
    用戶適配器類
    負責在SSO用戶和Django用戶之間進行轉換和同步
    
    使用場景：
    - 當模型使用 ForeignKey('auth.User') 時
    - 需要將 request.user（SSO User）轉換為 Django User 實例
    
    使用方法：
        from lungfung_sso import UserAdapter
        
        # 在視圖中
        django_user = UserAdapter.get_or_create_django_user(request.user)
        invoice.created_by = django_user
    """
    
    @staticmethod
    def get_or_create_django_user(sso_user):
        """
        根據SSO用戶獲取或創建對應的Django用戶
        
        參數:
            sso_user: SSO用戶實例 (lungfung_sso.models.User)
            
        返回:
            Django用戶實例，如果 sso_user 為空或已經是 Django User 則返回原值
        """
        if not sso_user:
            logger.warning("SSO用戶為空，返回None")
            return None
        
        User = get_user_model()
        
        # 如果已經是 Django User 實例，直接返回
        if isinstance(sso_user, User):
            return sso_user
        
        # 檢查是否為 SSO User（有 token 屬性但沒有 _state 屬性）
        if not UserAdapter.is_sso_user(sso_user):
            logger.warning(f"非SSO用戶類型: {type(sso_user)}")
            return None
            
        try:
            with transaction.atomic():
                # 嘗試根據用戶名獲取現有用戶
                try:
                    django_user = User.objects.get(username=sso_user.username)
                    logger.debug(f"找到現有Django用戶: {sso_user.username}")
                    
                    # 更新用戶信息以保持同步
                    UserAdapter._update_django_user(django_user, sso_user)
                    
                except User.DoesNotExist:
                    # 創建新的Django用戶
                    django_user = UserAdapter._create_django_user(sso_user)
                    logger.info(f"創建新的Django用戶: {sso_user.username}")
                
                return django_user
                
        except Exception as e:
            logger.error(f"獲取或創建Django用戶時發生錯誤: {str(e)}", exc_info=True)
            return None
    
    @staticmethod
    def _create_django_user(sso_user):
        """
        根據SSO用戶創建Django用戶
        
        參數:
            sso_user: SSO用戶實例
            
        返回:
            新創建的Django用戶實例
        """
        User = get_user_model()
        
        django_user = User.objects.create_user(
            username=sso_user.username,
            email=getattr(sso_user, 'email', '') or '',
            first_name=getattr(sso_user, 'first_name', '') or '',
            last_name=getattr(sso_user, 'last_name', '') or '',
            is_active=getattr(sso_user, 'is_active', True),
            is_staff=getattr(sso_user, 'is_staff', False),
            is_superuser=getattr(sso_user, 'is_superuser', False)
        )
        
        return django_user
    
    @staticmethod
    def _update_django_user(django_user, sso_user):
        """
        更新Django用戶信息以與SSO用戶保持同步
        
        參數:
            django_user: Django用戶實例
            sso_user: SSO用戶實例
        """
        updated = False
        
        # 檢查並更新基本信息
        email = getattr(sso_user, 'email', '') or ''
        if django_user.email != email:
            django_user.email = email
            updated = True
            
        first_name = getattr(sso_user, 'first_name', '') or ''
        if django_user.first_name != first_name:
            django_user.first_name = first_name
            updated = True
            
        last_name = getattr(sso_user, 'last_name', '') or ''
        if django_user.last_name != last_name:
            django_user.last_name = last_name
            updated = True
            
        is_active = getattr(sso_user, 'is_active', True)
        if django_user.is_active != is_active:
            django_user.is_active = is_active
            updated = True
            
        is_staff = getattr(sso_user, 'is_staff', False)
        if django_user.is_staff != is_staff:
            django_user.is_staff = is_staff
            updated = True
            
        is_superuser = getattr(sso_user, 'is_superuser', False)
        if django_user.is_superuser != is_superuser:
            django_user.is_superuser = is_superuser
            updated = True
        
        if updated:
            django_user.save()
            logger.debug(f"更新Django用戶信息: {sso_user.username}")
    
    @staticmethod
    def get_user_display_name(user):
        """
        獲取用戶顯示名稱
        支持SSO用戶和Django用戶
        
        參數:
            user: 用戶實例（SSO或Django）
            
        返回:
            用戶顯示名稱
        """
        if not user:
            return "未知用戶"
            
        # 如果是SSO用戶，優先使用 display_name
        if hasattr(user, 'display_name') and user.display_name:
            return user.display_name
        elif hasattr(user, 'get_full_name') and callable(user.get_full_name):
            full_name = user.get_full_name()
            if full_name:
                return full_name
                
        # 嘗試組合 first_name 和 last_name
        if hasattr(user, 'first_name') and hasattr(user, 'last_name'):
            if user.first_name and user.last_name:
                return f"{user.first_name} {user.last_name}"
            elif user.first_name:
                return user.first_name
            elif user.last_name:
                return user.last_name
                
        # 最後返回用戶名
        return getattr(user, 'username', '未知用戶')
    
    @staticmethod
    def is_sso_user(user):
        """
        檢查是否為SSO用戶
        
        參數:
            user: 用戶實例
            
        返回:
            bool: 是否為SSO用戶
        """
        if not user:
            return False
            
        # SSO 用戶有這些特有屬性，但沒有 Django 模型的 _state 屬性
        return (hasattr(user, 'modules') and 
                hasattr(user, 'permissions') and 
                hasattr(user, 'token') and
                not hasattr(user, '_state'))
    
    @staticmethod
    def get_user_info_dict(user):
        """
        獲取用戶信息字典，適用於保存到 JSONField 或日誌 context
        
        參數:
            user: 用戶實例（SSO或Django）
            
        返回:
            dict: 用戶信息字典
        """
        if not user:
            return None
            
        return {
            'id': getattr(user, 'id', None),
            'username': getattr(user, 'username', str(user)),
            'email': getattr(user, 'email', None),
            'display_name': UserAdapter.get_user_display_name(user),
            'is_sso_user': UserAdapter.is_sso_user(user),
        }

