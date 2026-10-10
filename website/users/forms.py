from django import forms
from django.contrib.auth import get_user_model

User = get_user_model()

class PasswordLinkForm(forms.Form):
    pass

class CurrentPasswordForm(forms.Form):
    current_password = forms.CharField(
        label="Поточгий пароль",
        widget=forms.PasswordInput(
            attrs={'autocomplete': 'current_password'}
        ),
    )

    def __init__(self, *args, user ,**kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_current_password(self):
        password = self.cleaned_data['current_password']

        if not self.user.check_password(password):
            raise forms.ValidationError(
                "Неправильний поточний пароль."
            )

        return password


class EmailUpdateForm(CurrentPasswordForm):
    new_email = forms.EmailField(
        label="Новий email",
        max_length=254,
    )

    def clean_new_email(self):
        email = self.cleaned_data["new_email"].strip()

        if email.casefold() == self.user.email.casefold():
            raise forms.ValidationError(
                "Це ваша поточна адреса."
            )

        if (
            get_user_model().objects
            .filter(email__iexact=email)
            .exclude(pk=self.user.pk)
            .exists()
        ):
            raise forms.ValidationError(
                "Ця адреса вже використовується."
            )

        return email