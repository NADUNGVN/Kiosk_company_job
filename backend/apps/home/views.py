# # -*- encoding: utf-8 -*-
# """
# Copyright (c) 2019 - present AppSeed.us
# """

# from django import template
# from django.contrib.auth.decorators import login_required
# from django.http import HttpResponse, HttpResponseRedirect
# from django.template import loader
# from django.urls import reverse
# from backend.customer.models import *
# # views.py
# from django.shortcuts import get_object_or_404
# from django.http import JsonResponse
# from backend.customer.models import Employee
# from .forms import EmployeeForm
# from django.views.decorators.csrf import csrf_exempt


# @login_required(login_url="/login/")
# def index(request):
    
#     if request.POST.get('btnCapNhat'):
#         employee_id = request.POST.get('id')
#         print(employee_id)
#         print('a')
#         # employee = Employee.objects.get(pk=employee_id)
#         # Cập nhật thông tin nhân viên từ dữ liệu được gửi từ form
#         # employee.name = request.POST.get('name')
#         # employee.status = request.POST.get('status')
#         # employee.service = request.POST.get('service')
#         # employee.save()
    
#     total_customer = ThongKe.objects.count()
#     danh_sach_nhan_vien = Employee.objects.all()
#     context = {'segment': 'index', 
#                'total_customer': total_customer,
#                'danh_sach_nhan_vien':danh_sach_nhan_vien,
#                }
#     html_template = loader.get_template('QRcodes/home/index.html')
#     return HttpResponse(html_template.render(context, request))


# @login_required(login_url="/login/")
# def pages(request):
#     context = {}
#     # All resource paths end in .html.
#     # Pick out the html file name from the url. And load that template.
#     try:

#         load_template = request.path.split('/')[-1]

#         if load_template == 'admin':
#             return HttpResponseRedirect(reverse('admin:index'))
#         context['segment'] = load_template

#         html_template = loader.get_template('home/' + load_template)
#         return HttpResponse(html_template.render(context, request))

#     except template.TemplateDoesNotExist:

#         html_template = loader.get_template('Qrcodes/home/page-404.html')
#         return HttpResponse(html_template.render(context, request))

#     except:
#         html_template = loader.get_template('home/page-500.html')
#         return HttpResponse(html_template.render(context, request))

# @csrf_exempt
# def edit_employee(request, pk):
#     employee = get_object_or_404(Employee, pk=pk)
#     if request.POST.get('btnCapNhat'):
#         ten = request.POST.get('name')
#         print(ten)
#         print('a')
#         form = EmployeeForm(request.POST, instance=employee)
#         if form.is_valid():
#             form.save()
#             return JsonResponse({'status': 'success'})
#         else:
#             return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)
    
#     return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)
