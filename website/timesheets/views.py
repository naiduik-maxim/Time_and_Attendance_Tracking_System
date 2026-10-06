from django.views.generic import ListView, DetailView
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.contrib.auth.mixins import UserPassesTestMixin
from .models import Tabel, ContentTabel
from unit.models import Unit
# Create your views here.

class AccountUnitListView(UserPassesTestMixin, ListView):
    model = Unit
    template_name = 'tabel/unit_select.html'
    context_object_name = 'units'

    def test_func(self):
        return self.request.user.is_superuser or self.request.user.groups.filter(name='Accountants').exists()

    def get_queryset(self):
        qs = super().get_queryset()
        if not self.request.user.is_superuser:
            qs = qs.filter(accountants = self.request.user)

        return qs

class TableListView(UserPassesTestMixin, ListView):
    model = Tabel
    template_name = 'tabel/tabel_list.html'
    context_object_name = 'tabels'

    ordering = ['-t_year', '-t_month']

    def test_func(self):
        return self.request.user.is_superuser or self.request.user.groups.filter(name='Accountants').exists()

    def get_queryset(self, queryset = None):

        self.unit = get_object_or_404(Unit, id=self.kwargs['unit_id'])

        if not self.request.user.is_superuser:
            if not self.unit.accountants.filter(id=self.request.user.id).exists():
                raise Http404("У вас немає прав для перегляду табеля цього підрозділу")

        return Tabel.objects.filter(unit=self.unit).order_by('-t_year', '-t_month')

class TabelDetailView(UserPassesTestMixin, DetailView):
    model = Tabel
    template_name = 'tabel/tabel_detail.html'
    context_object_name = 'tabel'

    def test_func(self):
            return self.request.user.is_superuser or self.request.user.groups.filter(name='Accountants').exists()


    def get_object(self, queryset = None):
        obj = super().get_object(queryset)

        if not self.request.user.is_superuser:
            if not obj.unit.accountants.filter(id=self.request.user.id).exists():
                 raise Http404("У вас немає прав для перегляду табеля цього підрозділу")

        return obj


    def get_context_data(self, **kwargs):
         context = super().get_context_data(**kwargs)

         context['records'] = ContentTabel.objects.filter(tabel=self.object).select_related('worker')
         return context

