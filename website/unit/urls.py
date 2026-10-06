from django.urls import path
from .views import UnitListView, UnitCreateView

urlpatterns = [
    path('', UnitListView.as_view(), name='unit_list'),
    path('create/', UnitCreateView.as_view(), name='unit_create'),
]