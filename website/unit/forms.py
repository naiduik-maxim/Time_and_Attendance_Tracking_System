from django import forms

from workers.models import Worker
from .models import Unit


class UnitForm(forms.ModelForm):
    class Meta:
        model = Unit
        fields = ['title', 'code', 'manager', 'address']


class WorkerHireForm(forms.ModelForm):
    class Meta:
        model = Worker
        fields = [
            'surname', 'firstname', 'lastname', 'id_passport', 'tabel_num',
            'phone_num', 'post', 'email', 'date_joined',
        ]
        widgets = {'date_joined': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d')}


class VacationLimitForm(forms.ModelForm):
    vacation_limit = forms.IntegerField(min_value=0, max_value=365, label='Днів відпустки')

    class Meta:
        model = Worker
        fields = ['vacation_limit']
