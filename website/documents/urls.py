from django.urls import path
from .views import DocumentCreateView, DocumentListView

urlpatterns = [
    path('', DocumentListView.as_view(), name='document_list'),
    path('create/', DocumentCreateView.as_view, name='document_create'),
]