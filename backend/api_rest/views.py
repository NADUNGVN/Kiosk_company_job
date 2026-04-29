from django.http import JsonResponse
from django.views.generic import View
from .serializers import KhachHangSerializer
from backend.customer.models import KhachHang

class KhachHangListView(View):
    def get(self, request):
        # Lấy tất cả các đối tượng KhachHang từ database
        khachhang_objects = KhachHang.objects.all()
        
        # Serialize dữ liệu
        serializer = KhachHangSerializer(khachhang_objects, many=True)
        
        # Trả về dữ liệu dưới dạng JSON
        return JsonResponse(serializer.data, safe=False)
    
    
# your_app/views.py

