from django.db import models
from backend.customer.models import Service

class Keyword(models.Model):
    word = models.TextField(blank=True, null=True)  # 
    counter = models.ForeignKey(Service, related_name='keywords', on_delete=models.CASCADE)
    is_bad_language = models.BooleanField(default=False)

    def __str__(self):
        return self.word
class ConversationLog(models.Model):
    user_input = models.TextField()
    bot_response = models.TextField()
    follow_up_question = models.TextField(default="")
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.timestamp}: {self.user_input} -> {self.bot_response}"
    
    
    
class Chat(models.Model):
    question = models.CharField(max_length=255)
    response = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class AllowedHost(models.Model):
    ip_address = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.ip_address

