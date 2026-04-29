from django import forms

from .models import Service, Employee, Manage, KhachHang
from .models import Banner


class BannerForm(forms.ModelForm):
    class Meta:
        model = Banner
        fields = ['name', 'image',]