from django.db import models
from datetime import datetime, timezone
from datetime import *
from django.utils import timezone



class ThongTinQR(models.Model):
    so_cccd = models.CharField(max_length=20)
    so_cmnd_cu = models.CharField(max_length=20)
    ho_va_ten = models.TextField(max_length=100)
    ngay_sinh = models.CharField(max_length=20)
    gioi_tinh = models.CharField(max_length=10)
    dia_chi = models.TextField(max_length=2000)
    ngay_cap = models.TextField(max_length=150)
    so_cccd_2 = models.CharField(max_length=20)
    so_cmnd_cu_2 = models.CharField(max_length=20)
    ho_va_ten_2 = models.TextField(max_length=100)
    ngay_sinh_2 = models.CharField(max_length=20)
    gioi_tinh_2 = models.CharField(max_length=10)
    dia_chi_2 = models.TextField(max_length=2000)
    ngay_cap_2 = models.TextField(max_length=150)
    so_cccd_3 = models.CharField(max_length=20)
    so_cmnd_cu_3 = models.CharField(max_length=20)
    ho_va_ten_3 = models.TextField(max_length=100)
    ngay_sinh_3 = models.CharField(max_length=20)
    gioi_tinh_3 = models.CharField(max_length=10)
    dia_chi_3 = models.TextField(max_length=2000)
    ngay_cap_3 = models.TextField(max_length=150)
    ngay_quet = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return self.ho_va_ten
# Create your models here.
class Customer(models.Model):
    first_name = models.CharField(max_length=264, blank=False)
    last_name = models.CharField(max_length=264, blank=False)
    email = models.EmailField(blank=False, unique=True)
    user_name=models.CharField(max_length=50, blank=False)
    password = models.CharField(max_length=50, blank=False)
    phone = models.CharField(max_length=20)
    address = models.TextField()

    def __str__(self):
        return self.last_name

# models.py

class Service(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    quay_so = models.IntegerField(null=True)
    image = models.ImageField(upload_to='QRcodes/images', default='QRcodes/images/default.png')
    is_active = models.BooleanField(default=True)
    prefix = models.IntegerField()  # Tiền tố của quầy
    is_hidden = models.BooleanField(default=True)
    now_serving_ticket = models.IntegerField(null=True, blank=True, help_text="Số thứ tự hiện đang được phục vụ tại quầy này")
    service_details = models.TextField(blank=True, help_text="Nhập mỗi dịch vụ 1 dòng")
    def __str__(self):
        return self.name
    
    

class Employee(models.Model):
    name = models.CharField(max_length=255)
    position = models.CharField(max_length=255)
    assigned_service = models.ForeignKey(Service, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    
class DichVuTungQuay(models.Model):
    
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    ten_thu_tuc = models.CharField(max_length=255)
    
    def __str__(self):
        return f'{self.service.name}'



class CapNhatDuLieu(models.Model):
    feedback = models.CharField(max_length=100)
    tong = models.CharField(max_length=20,null=True,blank=True)
    thong_bao = models.TextField(null=True,blank=True)
    
    def __str__(self):
        return self.feedback
    

class TrangThai(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

class KhachHang(models.Model):
    name = models.CharField(max_length=255, null=True)
    dia_chi = models.TextField(max_length=1000, null=True)
    so_cccd = models.CharField(max_length=15, null=True)
    ngay_sinh = models.CharField(max_length=255, null=True)
    gioi_tinh = models.CharField(max_length=10,null=True)
    ngay_cap = models.TextField(max_length=150,null=True)
    ticket_number = models.IntegerField(null=True)
    ho_ten_cha=models.CharField(max_length=255, null=True)
    ho_ten_me =models.CharField(max_length=255, null=True)
    employee = models.CharField(max_length=10, null=True)
    is_calling = models.BooleanField(default=False)
    is_called = models.BooleanField(default=False)
    feedback = models.CharField(max_length=10, null=True)
    service = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True)  # Liên kết với mô hình Service
    trang_thai = models.BooleanField(default=True)
    def __str__(self):
        return str(self.ticket_number)
    
    
class DanhSachCho(models.Model):
    khach_hang = models.OneToOneField(KhachHang, on_delete=models.CASCADE, related_name='danh_sach_cho')
    name = models.CharField(max_length=255, null=True)
    ticket_number = models.IntegerField(null=True)
    employee = models.IntegerField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Danh sách chờ của {self.khach_hang.name}"



class ThongKe(models.Model):
    name = models.CharField(max_length=255,null=True)
    dia_chi = models.TextField(max_length=1000, null=True)
    so_cccd = models.CharField(max_length=15, null=True)
    ngay_sinh = models.CharField(max_length=25, null=True)
    ticket_number = models.IntegerField(null=True)
    feedback = models.CharField(max_length=100, null=True)
    service = models.CharField(max_length=100, null=True)
    ngay_quet = models.DateTimeField(null=True)
    def __str__(self):
        return self.name if self.name else "Tên không xác định" 

class Manage(models.Model):
    name  = models.CharField(max_length=255,null=True)
    image = models.ImageField(upload_to='QRcodes/images/', default='QRcodes/images/default.png')
    time  = models.CharField(max_length=255,null=True)
    def __str__(self):
        return self.name

class Banner(models.Model):
    name  = models.CharField(max_length=255,null=True)
    image = models.ImageField(upload_to='customer/images/', default='customer/images/default.png')
    
    def __str__(self):
        return self.name
