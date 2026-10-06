from django.urls import path
from .views import TabelDetailView, TableListView, AccountUnitListView

urlpatterns = [
    path('', AccountUnitListView.as_view(), name='accountant_unit_list'),
    path('unit/<int:unit_id>/', TableListView.as_view(), name='tabel_list'),
    path('<int:pk>/', TabelDetailView.as_view(), name='tabel_detail'),
]