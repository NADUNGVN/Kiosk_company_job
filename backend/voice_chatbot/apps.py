# import asyncio
# from django.apps import AppConfig
# from django.conf import settings
# from asgiref.sync import sync_to_async

# class VoiceChatbotConfig(AppConfig):
#     name = 'backend.voice_chatbot'

#     def ready(self):
#         # Lấy event loop hiện tại và tạo task cho coroutine
#         loop = asyncio.get_running_loop()
#         loop.create_task(self.update_allowed_hosts_async())

#     async def update_allowed_hosts_async(self):
#         await sync_to_async(self.update_allowed_hosts)()

#     def update_allowed_hosts(self):
#         from .models import AllowedHost
#         settings.ALLOWED_HOSTS.extend([host.ip_address for host in AllowedHost.objects.all()])
