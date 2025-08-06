from django import forms
from .models import DailyRecord

class DailyRecordForm(forms.ModelForm):
    class Meta:
        model = DailyRecord
        fields = '__all__'
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }
