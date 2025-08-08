from django import forms
from .models import DailyRecord

class DailyRecordForm(forms.ModelForm):
    class Meta:
        model = DailyRecord
        fields = '__all__'
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'max_pressure': forms.NumberInput(attrs={'step': '0.1'}),
            'min_pressure': forms.NumberInput(attrs={'step': '0.1'}),
            'max_temperature': forms.NumberInput(attrs={'step': '0.1'}),
            'min_temperature': forms.NumberInput(attrs={'step': '0.1'}),
            'humidity': forms.NumberInput(attrs={'step': '1'}),
        }
