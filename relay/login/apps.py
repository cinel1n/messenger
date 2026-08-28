from django.apps import AppConfig
from django.core.signals import *

class LoginConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'login'

    def ready(self):
        from  . import signals
