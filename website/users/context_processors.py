from .forms import EmailUpdateForm, PasswordLinkForm
from unit.models import Unit


def profile_forms(request):
    if request.user.is_authenticated:
        return {
            "email_form": EmailUpdateForm(
                user=request.user,
                prefix="email",
            ),
            "password_form": PasswordLinkForm(
                prefix="password",
            ),
        }

    return {}


def navigation_links(request):
    if not request.user.is_authenticated:
        return {'has_worker_access': False, 'has_accountant_access': False, 'has_manager_access': False}

    return {
        'has_worker_access': request.user.groups.filter(name='Workers').exists(),
        'has_accountant_access': Unit.objects.filter(accountants=request.user).exists(),
        'has_manager_access': request.user.is_superuser or request.user.groups.filter(name='Managers').exists(),
    }
