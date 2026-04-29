from django.apps import AppConfig

from django.apps import AppConfig
from django.db.backends.signals import connection_created
from django.dispatch import receiver
class SetTimesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'backend.set_times'

    
    # def ready(self):
    #     # Kết nối tín hiệu khi có kết nối cơ sở dữ liệu
    #     @receiver(connection_created)
    #     def start_scheduler(sender, **kwargs):
    #         from . import scheduler
    #         scheduler.start()


