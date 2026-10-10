from .forms import EmailUpdateForm, PasswordLinkForm


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