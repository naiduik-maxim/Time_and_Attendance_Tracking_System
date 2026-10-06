from django.contrib import admin
from .models import Tabel, ContentTabel
# Register your models here.

class ContentTabelInline(admin.TabularInline):
    model = ContentTabel
    extra = 1


@admin.register(Tabel)
class TabelAdmin(admin.ModelAdmin):
    list_display = ('__str__','unit', 't_month', 't_year')
    list_filter = ('unit', 't_month', 't_year')
    inlines = (ContentTabelInline, )


@admin.register(ContentTabel)
class ContentTabelAdmin(admin.ModelAdmin):
    list_display = ('tabel', 'worker', 'count_work_day', 'vacation', 'hospital')
    list_filter = ('tabel__t_month', 'tabel__t_year')