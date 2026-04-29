# from apscheduler.schedulers.background import BackgroundScheduler
# from django.utils import timezone
# from backend.customer.models import Employee, Service
# from backend.set_times.models import SchedulerConfig

# def activate_all():
#     Employee.objects.update(is_active=True)
#     Service.objects.update(is_active=True)
#     print("Updated is_active to True for Employee and Service models at:", timezone.now())

# def start():
#     scheduler = BackgroundScheduler()
#     configs = SchedulerConfig.objects.all()
    
#     for config in configs:
#         scheduler.add_job(activate_all, 'cron', hour=config.hour, minute=config.minute)
#         print(f"Scheduled activate_all at {config.hour}:{config.minute}")
        
#     scheduler.start()

