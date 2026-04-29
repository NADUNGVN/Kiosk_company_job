from django.urls import path
from .views import KhachHangListView

app_name = 'api_rest'
urlpatterns = [
    path('api/khachhang/', KhachHangListView.as_view(), name='khachhang-list'),
    # Các URL pattern khác nếu cần
]
