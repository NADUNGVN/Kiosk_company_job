# voice_chatbot/urls.py
from django.urls import path
from backend.voice_chatbot.views import *
app_name = 'voice_chatbot'
urlpatterns = [
    path('voice', index, name='index'),
    path('listen/', listen, name='listen'),
    path('keyword_check/',keyword_check, name='keyword_check'),
    path('test_audio/', test_audio, name='get_audio'),
    path('process_request/',process_request, name='process_request'),
    # path('chat_bot', chatbot_view, name='chatbot'),
    # path('chat_bot_1',chatbot_view_1, name='chatbot'),
    path('select_counter/',select_counter, name='select_counter'),
    path('keyword_check/<int:pk>/',keyword_check, name='keyword_check'),
    path('add_keyword/<int:pk>/', add_keyword, name='add_keyword'),
    path('update_keyword/<int:pk>/',update_keyword, name='update_keyword'),
    path('delete_keyword/<int:pk>/',delete_keyword, name='delete_keyword'),
    path('add_ip',manage_allowed_hosts, name='manage_allowed_hosts'),
    path('delete_ip/<int:pk>',delete_allowed_host, name='delete_allowed_host'),
    

]
