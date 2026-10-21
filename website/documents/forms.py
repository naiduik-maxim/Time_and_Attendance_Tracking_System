from django.core.exceptions import ValidationError
from django.forms import ModelForm, DateInput, Textarea, NumberInput
from timesheets.services import TYPE_TO_FIELD, iter_counted_days, normalize_type
from .models import Document

class DocumentForm(ModelForm):
    def __init__(self, *args, worker=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.worker = worker

    def clean_type_missing(self):
        missing_type = self.cleaned_data['type_missing']
        if normalize_type(missing_type.name) not in TYPE_TO_FIELD:
            raise ValidationError('Невідомий тип відсутності для табеля.')
        return missing_type

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('date_start')
        end = cleaned_data.get('date_end')
        count = cleaned_data.get('count_day')

        if not start or not end:
            return cleaned_data
        if end < start:
            self.add_error('date_end', 'Кінцева дата не може бути раніше початкової.')
            return cleaned_data

        expected_count = sum(1 for _ in iter_counted_days(start, end))
        if expected_count == 0:
            self.add_error('date_end', 'У вибраному періоді немає робочих днів.')
        elif count is not None and count != expected_count:
            self.add_error('count_day', f'Для вибраного періоду потрібно вказати {expected_count} робочих днів.')

        if self.worker is not None:
            if start < self.worker.date_joined:
                self.add_error('date_start', 'Дата не може бути раніше прийому на роботу.')
            overlapping = Document.objects.filter(
                worker=self.worker,
                date_start__lte=end,
                date_end__gte=start,
            )
            if self.instance.pk:
                overlapping = overlapping.exclude(pk=self.instance.pk)
            if overlapping.exists():
                self.add_error('date_start', 'На цей період уже є документ.')

        return cleaned_data

    class Meta:
        model = Document
        fields = ['type_missing', 'date_start', 'date_end', 'description', 'count_day']
        widgets = {
            'date_start': DateInput(attrs={'type': 'date'}),
            'date_end': DateInput(attrs={'type': 'date'}),
            'description': Textarea(attrs={'rows': 3}),
            'count_day': NumberInput(attrs={'min': '1'}),
        }
