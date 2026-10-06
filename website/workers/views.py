from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import UserPassesTestMixin
from .models import Worker
# Create your views here.

class WorkerCreateView(UserPassesTestMixin, CreateView):
    model = Worker
    template_name = 'worker_worker_form.html'
    fields = ['surname', 'firstname', 'id_passport', 'tabel_num', 'post', 'unit']
    success_url = reverse_lazy('manager_view')

    def test_func(self):
        return self.request.user.is_superuser or self.request.user.groups.filter(name='Managers').exists()
