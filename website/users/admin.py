from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User
from workers.models import Worker
# Register your models here.

class WorkerInline(admin.StackedInline):
    model = Worker
    can_delete = False
    verbose_name_plural = 'Профіль працівника'
    fk_name = 'user'


@admin.register(User)
class CustomerUserAdmin(UserAdmin):
    inlines = (WorkerInline,)

    list_display = ('username', 'first_name', 'last_name', 'is_staff', 'get_worker_post')

    def get_worker_post(seld, obj):
        if hasattr(obj, 'worker_profile') and obj.worker_profile:
            return obj.worker_profile.post
        return "-"
    get_worker_post.short_description = 'Посада'
