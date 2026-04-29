from django.urls import path
from . import views
app_name = 'qrcode'
urlpatterns = [
    path('login', views.login, name = 'login'),
    path('trang-chu-1', views.index_1, name = 'trang-chu-1'),
    path('a', views.index_1, name='trang_chu_1'),
    path('trang_chu_1', views.index, name='trang-chu'),
    path('xu_ly/<int:pk>/',views.export, name='xu_ly'),
    path('chon_don_1', views.chon_don_1, name='chon-don'),
    path('chon_don_2', views.chon_don_2, name='chon-don-2'),
    path('don_1_nguoi', views.don_1_nguoi, name='don-1-nguoi'),
    path('don_2_nguoi', views.don_2_nguoi, name='don-2-nguoi'),
    path('don_3_nguoi', views.don_khai_sinh, name='khai-sinh'),
    path('khai_sinh_1', views.khai_sinh_1, name='khai-sinh-1'),
    path('khai_tu', views.don_khai_tu, name ='khai-tu'),
    path('khai_tu_1', views.khai_tu_1, name='khai-tu-1'),
    path('ket_hon_1', views.ket_hon_1, name='ket-hon-1'),
    path('ho_tich_1', views.trich_luc_ho_tich_1, name='ho-tich-1'),
    path('ho_tich_2', views.trich_luc_ho_tich_2, name='ho-tich-2'),
    path('hon_nhan_1', views.xac_nhan_hon_nhan, name='hon-nhan-1'),
    path('hon_nhan_2', views.xac_nhan_hon_nhan_2, name='hon-nhan-2'),
    path('file', views.upload_file, name='upload'),
    path('data_qr', views.quet_3_nguoi, name='quet-3-nguoi'),
    path('file_1', views.run_word_macro, name='upload_1'),
    # path('scan', views.scan_QR, name='test'),
    path('don_ket_hon', views.ket_hon, name='ket-hon'),



    
]
