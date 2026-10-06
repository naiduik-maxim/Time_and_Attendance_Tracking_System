from django.contrib.auth.mixins import UserPassesTestMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView
from .models import Document
# Create your views here.

class DocumentListView(UserPassesTestMixin, ListView):
    model = Document
    template_name = 'document/document_list.html'
    context_object_name = 'documents'

    def test_func(self):
        return self.request.user.groups.filter(name='Workers').exists()

    def get_queryset(self):
        return Document.objects.filter(worker=self.request.user.worker_profile).order_by('-date_start')

class DocumentCreateView(UserPassesTestMixin, CreateView):
    model = Document
    template_name = 'document/document_create.html'
    fields = ('type_missing', 'date_start', 'date_end', 'description', 'count_day')
    success_url = reverse_lazy('document_list')

    def test_func(self):
            return self.request.user.groups.filter(name='Workers').exists()

    def form_valid(self, form):
         form.instance.worker = self.request.user.worker_profile
         return super().form_valid(form) 
