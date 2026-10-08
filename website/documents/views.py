from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.utils import timezone
from django.db.models import Sum
from django.views.generic import ListView, CreateView
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
        
        current_year = timezone.now().year
        user_docs_this_year = Document.objects.filter(
            worker__user=self.request.user, 
            date_start__year=current_year
        )

        booked_dates = []

        for doc in user_docs_this_year:
            if doc.date_start and doc.date_end:
                booked_dates.append(
                    {'start': doc.date_start.strftime('%Y-%m-%d'),
                    'end': doc.date_end.strftime('%Y-%m-%d')
                    })


        context['booked_dates'] = json.dumps(booked_dates)

        vacation_used = user_docs_this_year.filter(type_missing__name='vacation').aggregate(Sum('count_day'))['count_day__sum'] or 0
        sick_used = user_docs_this_year.filter(type_missing__name='hospital').aggregate(Sum('count_day'))['count_day__sum'] or 0

    
        LIMIT_VACATION = self.request.user.vacation_limit
        LIMIT_SICK = self.request.user.sick_limit


        context['vacation_left'] = max(0, LIMIT_VACATION - vacation_used)
        context['sick_left'] = max(0, LIMIT_SICK - sick_used)
        context['form'] = DocumentForm()
        
        return context


class DocumentCreateView(UserPassesTestMixin, CreateView):
    model = Document
    form_class = DocumentForm  
    success_url = reverse_lazy('document_list')

    def test_func(self):
        return self.request.user.groups.filter(name='Workers').exists()

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
        
        return super().form_valid(form)

    def form_invalid(self, form):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'error',
                'errors': form.errors
            }, status=400)
        return super().form_invalid(form)
