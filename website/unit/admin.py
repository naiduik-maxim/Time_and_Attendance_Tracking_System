from django.contrib import admin
from .models import Unit
from workers.models import Worker
# Register your models here.

class WorkerInline(admin.TabularInline):
    model = Worker
    extra = 0
    fields = ('tabel_num', 'surname', 'firstname', 'date_joined')
    show_change_link = True


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ('title', 'code', 'manager', 'address', 'count_workers')
    search_fields = ('title', 'code')
    inlines = (WorkerInline,)