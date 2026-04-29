from rest_framework import routers, serializers, viewsets
from rest_framework.serializers import ModelSerializer
from django.db import models
from backend.customer.models import KhachHang, ThongTinQR
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from rest_framework import serializers
from .models import CustomUser

class KhachHangSerializer(ModelSerializer):
    class Meta:
        model = KhachHang
        fields = ["id", "name", "ticket_number", "is_calling", "is_called","employee_id" ]
    
class ThongTinQRSertializer(ModelSerializer):
    class Meta:
        model= ThongTinQR
        fields = '__all__'
        




class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ('id', 'username', 'email', 'password')
        extra_kwargs = {'password': {'write_only': True}}


        
