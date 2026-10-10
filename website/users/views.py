from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.contrib.auth.views import LoginView, LogoutView
from django.core.exceptions import PermissionDenied
from django.urls import reverse_lazy, reverse
# Create your views here.

class UserLoginView(LoginView):
    template_name = 'users/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        user = self.request.user
        
        if user.is_superuser:
            return reverse('admin:index')
            
        if user.groups.filter(name='Accountants').exists():
            return reverse('accountant_unit_list') 
            
        elif user.groups.filter(name='Managers').exists():
            return reverse('unit_list')
            
        elif user.groups.filter(name='Workers').exists():
            return reverse('document_list')
            
        raise PermissionDenied("Вашому акаунту не призначено жодної системної ролі. Зверніться до адміністратора.")


class UserLogoutView(LogoutView):
    next_page = reverse_lazy('login')