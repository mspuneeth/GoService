from django import forms
from .models import Service

class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ['profession_name', 'image']
        widgets = {
            'profession_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Profession Name'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }
