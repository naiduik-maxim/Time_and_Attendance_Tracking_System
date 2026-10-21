from django.urls import path
from .views import ManagerDashboardView, ManagerDepartmentView, UnitListView, UnitCreateView

urlpatterns = [
    path('manager/', ManagerDashboardView.as_view(), name='manager_dashboard'),
    path('manager/<int:pk>/', ManagerDepartmentView.as_view(), name='manager_department'),
    path('', UnitListView.as_view(), name='unit_list'),
    path('create/', UnitCreateView.as_view(), name='unit_create'),
]
