# forms.py
from django import forms
from backend.customer.models import Employee

class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ['name', 'position', 'is_active', 'assigned_service']
        # Các trường thông tin muốn chỉnh sửa

       
