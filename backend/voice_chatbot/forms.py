# myapp/forms.py
from django import forms
from backend.customer.models import Service

class TextForm(forms.Form):
    text = forms.CharField(widget=forms.Textarea, label='Nhập văn bản')

from django import forms
from .models import Keyword

class KeywordForm(forms.ModelForm):
    is_bad_language = forms.BooleanField(required=False, label='Từ ngữ xấu')

    class Meta:
        model = Keyword
        fields = ['word', 'is_bad_language']

class TextForm(forms.Form):
    text = forms.CharField(widget=forms.Textarea, label='Nhập văn bản')

# forms.py
from django import forms
from .models import AllowedHost

class AllowedHostForm(forms.ModelForm):
    class Meta:
        model = AllowedHost
        fields = ['ip_address']
