from django import forms
from .models import Department, CustomUser

class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name', 'code', 'description', 'manager', 'location', 'is_active']

        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Enter department name'}),
            'code': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Optional department code'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'placeholder': 'Optional description', 'rows': 4}),
            'manager': forms.Select(attrs={'class': 'form-input'}),
            'location': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Optional location'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }