from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import ListView, CreateView
from datetime import date

from timesheets.services import TYPE_TO_FIELD, iter_counted_days, normalize_type
from .forms import DocumentForm
from .models import Document
import json
# Create your views here.

class DocumentListView(UserPassesTestMixin, ListView):
    model = Document
    template_name = 'document/document_list.html'
    context_object_name = 'documents'

    def test_func(self):
        return self.request.user.groups.filter(name='Workers').exists()

    def get_queryset(self):
        return Document.objects.filter(worker=self.request.user.worker_profile).order_by('-date_start')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        current_year = timezone.localdate().year
        year_start = date(current_year, 1, 1)
        year_end = date(current_year, 12, 31)
        user_docs_this_year = Document.objects.filter(
            worker__user=self.request.user, 
            date_start__lte=year_end,
            date_end__gte=year_start,
        ).select_related('type_missing')

        booked_dates = []
        vacation_used = 0
        sick_used = 0

        for doc in user_docs_this_year:
            if doc.date_start and doc.date_end:
                booked_dates.append(
                    {'start': doc.date_start.strftime('%Y-%m-%d'),
                    'end': doc.date_end.strftime('%Y-%m-%d')
                    })

                counted_days = sum(1 for _ in iter_counted_days(
                    max(doc.date_start, year_start),
                    min(doc.date_end, year_end),
                ))
                field = TYPE_TO_FIELD.get(normalize_type(doc.type_missing.name))
                if field == 'vacation':
                    vacation_used += counted_days
                elif field == 'hospital':
                    sick_used += counted_days


        context['booked_dates'] = json.dumps(booked_dates)

        LIMIT_VACATION = self.request.user.worker_profile.vacation_limit
        LIMIT_SICK = self.request.user.sick_limit


        context['vacation_left'] = max(0, LIMIT_VACATION - vacation_used)
        context['sick_left'] = max(0, LIMIT_SICK - sick_used)
        context['form'] = DocumentForm()
        
        return context


class DocumentCreateView(UserPassesTestMixin, CreateView):
    model = Document
    form_class = DocumentForm  
    success_url = reverse_lazy('document_list')
    http_method_names = ['post']

    def test_func(self):
        return self.request.user.groups.filter(name='Workers').exists()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['worker'] = self.request.user.worker_profile
        return kwargs

    def form_valid(self, form):
        form.instance.worker = self.request.user.worker_profile

        self.object = form.save()

        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'document': {
                    'type_missing': str(self.object.type_missing),
                    'date_start_display': self.object.date_start.strftime('%d.%m.%Y'),
                    'date_end_display': self.object.date_end.strftime('%d.%m.%Y'),
                    'date_start_raw': self.object.date_start.strftime('%Y-%m-%d'),
                    'date_end_raw': self.object.date_end.strftime('%Y-%m-%d'),
                    'count_day': self.object.count_day,
                    'description': self.object.description or '-'
                }
            })
        
        return redirect(self.get_success_url())

    def form_invalid(self, form):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'error',
                'errors': form.errors
            }, status=400)
        messages.error(self.request, 'Документ не збережено. Перевірте дати та кількість робочих днів.')
        return redirect('document_list')
