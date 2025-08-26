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
        
    Example:
        configure_sso_settings(globals(), {
            'SSO_SERVER_URL': 'http://localhost:8000',
            'MODULE_CODE': 'TAICHENG',
            'VERIFY_SSL': True,
            'REQUEST_TIMEOUT': 5,
            'CHILD_MODULES': {
                'TRANSFER_ORDER': 'to',
                'SYSTEM': 'system',
            },
            'PARENT_PERMISSIONS': {
                'VIEW_SYSTEM': 'view_taicheng_system',
                'MANAGE_SYSTEM': 'manage_taicheng_system',
            }
        })
    """
    default_config = {
        'SSO_SERVER_URL': 'http://localhost:8000',
        'MODULE_CODE': 'DEFAULT',
        'VERIFY_SSL': True,
        'REQUEST_TIMEOUT': 5,
        'CHILD_MODULES': {},
        'PARENT_PERMISSIONS': {
            'VIEW_SYSTEM': 'view_default_system',
            'MANAGE_SYSTEM': 'manage_default_system',
        },
        'CHILD_PERMISSION_TYPES': {
            'VIEW': 'view',
            'ADD': 'add', 
            'CHANGE': 'change',
            'DELETE': 'delete',
        }
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
        'CHILD_MODULES': default_config['CHILD_MODULES'],
    }
    
    # 設置權限配置
    settings_dict['SSO_PERMISSIONS'] = {
        'PARENT_PERMISSIONS': default_config['PARENT_PERMISSIONS'],
        'CHILD_PERMISSION_TYPES': default_config['CHILD_PERMISSION_TYPES']
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
