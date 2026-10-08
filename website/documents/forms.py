from django.forms import ModelForm, DateInput, Textarea, NumberInput
from .models import Document

class DocumentForm(ModelForm):
    class Meta:
        model = Document
        fields = ['type_missing', 'date_start', 'date_end', 'description', 'count_day']
        widgets = {
            'date_start': DateInput(attrs={'type': 'date'}),
            'date_end': DateInput(attrs={'type': 'date'}),
            'description': Textarea(attrs={'rows': 3}),
            'count_day': NumberInput(attrs={'min': '1'}),
        }