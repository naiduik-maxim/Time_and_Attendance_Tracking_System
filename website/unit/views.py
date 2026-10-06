from django.views.generic import ListView, CreateView
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.urls import reverse_lazy
from .models import Unit
# Create your views here.

class UnitListView(LoginRequiredMixin, ListView):
    model = Unit
    template_name = 'unit/unit_list.html'
    context_object_name = 'units'


class UnitCreateView(UserPassesTestMixin, CreateView):
    model = Unit,
    template_name = 'unit/unit_create.html'
    fields = ['title', 'code', 'manager']
    success_url = reverse_lazy('unit_list')

    def test_func(self):
        return self.request.user.is_superuser or self.request.user.groups.filter(name='Managers').exists()
