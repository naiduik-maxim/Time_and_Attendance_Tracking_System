from django.urls import path, include
from .views import UserLoginView, UserLogoutView
from .profile_views import (
    ProfileView,
    ProfilePageView,
    ProfileEmailConfirmView,
)
from django.contrib.auth import views as auth_views

urlpatterns = [
    path(
        "login/",
        UserLoginView.as_view(),
        name="login",
    ),
    path(
        "logout/",
        UserLogoutView.as_view(),
        name="logout",
    ),
    path(
        "my-profile/",
        ProfilePageView.as_view(),
        name="profile_page",
    ),
    path(
        "profile/modal/",
        ProfileView.as_view(),
        name="profile",
    ),
    path(
        "profile/email/confirm/<str:token>/",
        ProfileEmailConfirmView.as_view(),
        name="profile_email_confirm",
    ),
    path(
        "profile/reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="users/password_reset_confirm.html",
        ),
        name="password_reset_confirm",
    ),
    path(
        "profile/reset/done/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="users/password_reset_complete.html",
        ),
        name="password_reset_complete",
    ),
    path(
        "profile/password_reset/",
        auth_views.PasswordResetView.as_view(
            template_name="users/password_reset_form.html",
            email_template_name="users/password_reset_email.html",
            subject_template_name="users/password_reset_subject.txt",
        ),
        name="password_reset",
    ),
    path(
        "profile/password_reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="users/password_reset_done.html",
        ),
        name="password_reset_done",
    ),
]