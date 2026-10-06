from django.contrib import admin
from .models import Worker
# Register your models here.

@admin.register(Worker)
class WorkerAdmin(admin.ModelAdmin):
    list_display = ('tabel_num', 'surname', 'firstname', 'lastname', 'unit', 'post', 'date_joined')
    search_fields = ('surname', 'tabel_num', 'id_passport')
    list_filter = ('unit', 'post')