from smtplib import SMTPException

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.tokens import (
    PasswordResetTokenGenerator,
    default_token_generator,
)
from django.core import signing
from django.core.cache import cache
from django.core.mail import send_mail
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.views import View
from django.views.generic import TemplateView
from django.views.decorators.cache import never_cache

from workers.models import Worker
from .forms import PasswordLinkForm, EmailUpdateForm


EMAIL_SALT = 'users.profile.email-change'

class EmailChangeTokenGenerator(PasswordResetTokenGenerator):
    key_salt = 'users.profile.EmailChangeTokenGenerator'

    def _make_hash_value(self, user, timestamp):
         return (
            f"{user.pk}:{user.password}:"
            f"{timestamp}:{user.email}"
        )

email_tokens = EmailChangeTokenGenerator()


class ProfilePageView(LoginRequiredMixin, TemplateView):
     login_url = 'login'
     template_name = 'users/profile_page.html'


@method_decorator(never_cache, name='dispatch')
class ProfileView(LoginRequiredMixin, View):
    login_url = 'login'

    def reply(
               self,
               email_form=None,
               password_form=None,
               notice='',
               status=200
     ):
          user = self.request.user

          html = render_to_string(
                'users/profile_modal.html',
                {
               'worker': getattr(user, 'worker_profile', None),
               'email_form': email_form or EmailUpdateForm(
                    user=user,
                    prefix="email",
                ),
                 "password_form": (
                    password_form
                    if password_form is not None
                    else PasswordLinkForm(prefix="password")
                ),
                "notice": notice,
                },
                request=self.request
          )

          return JsonResponse({'html': html}, status=status)

    def get(self, request):
        return self.reply()

    def post(self, request):
        user = request.user
        action = request.POST.get('action')

        if action not in {'email', 'password'}:
            return self.reply(notice="Невідома дія", status=400)

        if action == "email":
            form = EmailUpdateForm(
                request.POST,
                user=user,
                prefix="email",
            )
        else:
            form = PasswordLinkForm(
                request.POST,
                prefix="password",
            )

        forms = {f"{action}_form": form}

        print("Дія:", action)
        print("Клас форми:", type(form).__name__)
        print("Поля з помилками:", list(form.errors))
        print("Email задано:", bool(user.email))
        print("Пароль доступний:", user.has_usable_password())
        
        if not form.is_valid():
            return self.reply(**forms, status=400)

        if action == 'password' and (
            not user.email or not user.has_usable_password()
        ):
            return self.reply(
                **forms,
                notice=(
                    "Для зміни пароля потрібен "
                    "email облікового запису."
                ),
                status=400,
            )

        key = f"profile-mail:{user.pk}:{action}"

        if not cache.add(key, True, timeout=60):
            return self.reply(
                **form,
                notice="Зачекайте хвилину перед повторним листом.",
                status=429,
            )

        if action == 'email':
            recipient = form.cleaned_data['new_email']

            token = signing.dumps(
                {
                    'uid': user.pk,
                    'email': recipient,
                    'state': email_tokens.make_token(user),
                },
                salt=EMAIL_SALT,
            )

            path = reverse(
                'profile_email_confirm',
                kwargs={'token': token},
            )

            subject = "TimeManager: підтвердження нового email"
            notice = (
                "Посилання надіслано на новий email. "
                "Підтвердьте його протягом години."
            )

        else:
            recipient = user.email

            path = reverse(
                'password_reset_confirm',
                kwargs={
                    'uidb64': urlsafe_base64_encode(
                        force_bytes(user.pk)
                    ),
                    'token': default_token_generator.make_token(user),
                },
            )

            subject = "TimeManager: зміна пароля"
            notice = (
                "Посилання для встановлення нового пароля "
                "надіслано на ваш email."
            )

            body = (
                f"{subject}\n\n"
                f"{request.build_absolute_uri(path)}\n\n"
                "Якщо ви не робили запит, проігноруйте лист."
            )

            try:
                sent = send_mail(
                    subject,
                    body,
                    settings.DEFAULT_FROM_EMAIL,
                    [recipient],
                )

                if sent != 1:
                    raise OSError("Email was not sent")

            except (SMTPException, OSError):
                cache.delete(key)

                return self.reply(
                    **forms,
                    notice="Не вдалося надіслати лист. Спробуйте пізніше.",
                    status=503,
                )
            
            return self.reply(notice=notice)


@method_decorator(never_cache, name='dispatch')
class ProfileEmailConfirmView(LoginRequiredMixin, View):
    login_url = 'login'

    def get_payload(self, token, user):
        try:
            data = signing.loads(
                token,
                salt=EMAIL_SALT,
                max_age=3600,
            )
        except signing.BadSignature:
            return None
        if (
            data['uid'] != user.pk
            or not email_tokens.check_token(user, data['state'])
        ):
            return None

        return data

    def get(self, request, token):
        data = self.get_payload(token, request.user)

        return render(
            request,
            "users/email_confirm.html",
            {"new_email": data["email"] if data else None},
        )

    def post(self, request, token):
        User = get_user_model()

        with transaction.atomic():
            user = User.objects.select_for_update().get(
                pk=request.user.pk
            )

            data = self.get_payload(token, user)

            if not data:
                messages.error(
                    request,
                    "Посилання недійсне, прострочене "
                    "або вже використане.",
                )

            elif (
                User.objects.filter(email_iexavt=data['email'])
                .exclude(pk=user.pk)
                .exists()
            ):
                messages.error(
                    request,
                    "Ця адреса вже використовується "
                    "іншим користувачем.",
                )

            else:
                user.email = data['email']
                user.save(update_fields=['email'])

                Worker.objects.filter(user=user).update(
                    email=user.email
                )

                messages.success(
                    request,
                    "Email успішно змінено.",
                )

        return redirect("profile_page")