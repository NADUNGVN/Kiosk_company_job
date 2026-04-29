from django.contrib import admin
from django.db.models import Sum
from django.db.models import Count  #
from .models import Service, Employee, Manage, KhachHang, TrangThai, ThongKe, CapNhatDuLieu, DichVuTungQuay,Customer
from import_export.admin import ImportExportModelAdmin
from rangefilter.filters import (
    DateRangeFilterBuilder,
    DateTimeRangeFilterBuilder,
    NumericRangeFilterBuilder,
    DateRangeQuickSelectListFilterBuilder,
    DateRangeFilter
)

class EmployeeInline(admin.TabularInline):  
    model = Employee
    extra = 1
    
    
    
class DichVuTungQuayInline(admin.TabularInline):
    model = DichVuTungQuay
    extra = 1


class ServiceAdmin(admin.ModelAdmin):
    
    
    inlines = [EmployeeInline,DichVuTungQuayInline]
    actions = ['make_active']
    # Thêm 'employee_names' vào list_display
    list_display = ('name','employee_names', 'is_active','quay_so','prefix','is_hidden')
 
    def make_active(self, request, queryset):
        queryset.update(is_active=True)
    make_active.short_description = "Activate selected services"
    def employee_names(self, instance):
        return ", ".join([employee.name for employee in instance.employee_set.all()])
    employee_names.short_description = 'Employee Names'

class ThongKeAdmin(ImportExportModelAdmin):
    encoding = 'utf-8'
    list_display = ('name', 'dia_chi', 'ticket_number', 'feedback', 'service', 'formatted_ngay_quet','ngay_sinh','so_cccd')
    search_fields = ('name', 'dia_chi', 'feedback', 'service', 'ngay_quet')
    

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(total_feedback=Count('feedback'))
        return queryset

    class Media:
        js = ('custom_admin.js',)
        
    def formatted_ngay_quet(self, obj):
        # Chuyển đổi giá trị ngay_quet thành định dạng "dd/mm/yyyy"
        return obj.ngay_quet.strftime("%d/%m/%Y") if obj.ngay_quet else None

    formatted_ngay_quet.short_description = 'Ngày Quét'  # Đặt tên cho cột
    list_filter = (
        ('ngay_quet', DateRangeFilter),  # Thêm DateRangeFilter cho trường ngay_quet
        'feedback', 
    )

class KhachHangAdmin(ImportExportModelAdmin):
    encoding = 'utf-8'
    
    change_list_template = 'change_list_graph.html'
    


    

admin.site.register(Customer)
admin.site.register(CapNhatDuLieu)
admin.site.register(ThongKe, ThongKeAdmin)
admin.site.register(Service, ServiceAdmin)
admin.site.register(Manage)
admin.site.register(TrangThai)
admin.site.register(KhachHang)
admin.site.register(DichVuTungQuay)
