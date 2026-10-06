from django.contrib import admin
from .models import Document, TypeMissing
# Register your models here.

@admin.register(TypeMissing)
class TypeMissingAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('worker', 'type_missing', 'date_start', 'date_end', 'description', 'count_day')
    list_filter = ('type_missing', 'date_start')
    search_fields = ('worker__surname', 'worker_tabel_num', 'description')
