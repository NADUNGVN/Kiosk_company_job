from django.urls import path
from backend.customer.views import *
from backend.QRcodes.views import *
from django.contrib.auth.decorators import login_required

app_name = 'customer'
urlpatterns = [
    path('dang_nhap',dang_nhap, name='dang-nhap'),
    path('',trang_chu_2, name='trang-chu'),
    path('danh_gia/<int:pk>/<int:id_khach_hang>/',danh_gia, name='danh_gia'),
    path('lay_so/<int:quay_so>/', get_ticket, name='lay-so'),
    path('gui_khach_hang/<int:pk>/<int:ticket_number>/',gui_khach_hang, name='gui-khach-hang'),
    path('bang_khach_hang',bang_khach_hang, name='bang-khach-hang'),
    path('chon_dich_vu',chon_dich_vu, name='chon-dich-vu'),
    path('nhan_vien/<int:assigned_service_id>/<int:id_nhan_vien>/',nhan_vien, name='nhan-vien'),
    path('tong_hop',tong_hop, name='tong-hop'),
    path('text_to_speech',text_to_speech, name='text_to_speech'),
    path('dem',dem,name='dem'),
    path('feedback-chart/', feedback_chart_data, name='feedback_chart_data'),
    path('move-to-waiting-list/<int:khachhang_id>/', move_to_waiting_list, name='move_to_waiting_list'),
    path('lay_so_1', lay_so, name='lay_so'),
    path('lam_thu_tuc', lam_thu_tuc, name='lam-thu-tuc'),
    path('dang_ky_ket_hon', dang_ky_ket_hon, name='dang-ky-ket-hon'),
    path('feedback_statistics/',feedback_statistics, name='feedback_statistics'),
    path('get_all_status/',get_all_status, name='get_all_status'),
    path('banners/', manage_banners, name='banner_list'),
    path('banner/', manage_banners, name='manage_banners'),
    path('banner/<int:banner_id>/', manage_banners, name='manage_banners'),
    path('xem_thong_ke/',show_thong_ke,name='xem_thong_ke'),
    path('lay_so_theo_quay/',create_khachhang,name='xem_thong_ke'),
    path('manage/ajax/',service_employee_management_ajax, name='service_employee_management_ajax'),
    path('danh_sach_nhan_vien/<int:assigned_service_id>/',danh_sach_nhan_vien, name='danh_sach_nhan_vien'),
]
   

# handler404 = 'customer.views.error_404_view'
# handler500 = 'customer.views.error_500_view'
    