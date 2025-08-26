from django.apps import AppConfig

class LungfungSsoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'lungfung_sso'
    verbose_name = 'LungFung SSO'
    
    def ready(self):
        """當 Django 應用準備就緒時執行"""
        pass