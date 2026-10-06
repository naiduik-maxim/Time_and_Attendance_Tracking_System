from django.urls import path
from .views import WorkerCreateView

urlpatterns = [
    path('hire/', WorkerCreateView.as_view(), name='worker_create'),
]