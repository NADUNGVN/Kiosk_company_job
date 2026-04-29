from django.db import models

class SchedulerConfig(models.Model):
    hour = models.IntegerField()  # Giờ
    minute = models.IntegerField(default=0)  # Phút mặc định là 0

    def __str__(self):
        return f"Scheduled at {self.hour}:{self.minute}"
