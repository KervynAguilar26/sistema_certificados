"""URLs del panel operativo."""

from __future__ import annotations

from django.contrib.auth import views as auth_views
from django.urls import path

from . import views
from .forms import PanelAuthenticationForm

app_name = "panel"

urlpatterns = [
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="panel/login.html",
            authentication_form=PanelAuthenticationForm,
            redirect_authenticated_user=True,
            next_page="panel:dashboard",
        ),
        name="login",
    ),
    path(
        "logout/",
        auth_views.LogoutView.as_view(next_page="panel:login"),
        name="logout",
    ),
    path("", views.dashboard, name="dashboard"),
    path("certificates/", views.certificate_list, name="certificate_list"),
    path(
        "certificates/new/",
        views.certificate_create,
        name="certificate_create",
    ),
    path(
        "certificates/<int:pk>/",
        views.certificate_detail,
        name="certificate_detail",
    ),
    path(
        "certificates/<int:pk>/edit/",
        views.certificate_edit,
        name="certificate_edit",
    ),
    path(
        "certificates/<int:pk>/pdf/<str:lang>/",
        views.certificate_pdf,
        name="certificate_pdf",
    ),
    path(
        "certificates/<int:pk>/html/<str:lang>/",
        views.certificate_html,
        name="certificate_html",
    ),
    path(
        "certificates/<int:pk>/qr/",
        views.certificate_qr,
        name="certificate_qr",
    ),
    path(
        "certificates/<int:pk>/status/",
        views.certificate_status,
        name="certificate_status",
    ),
    path(
        "certificates/<int:pk>/regenerate-token/",
        views.certificate_regenerate_token,
        name="certificate_regenerate_token",
    ),
    path("activity/", views.activity, name="activity"),
    path("users/", views.user_list, name="user_list"),
    path("users/new/", views.user_create, name="user_create"),
    path("users/<int:pk>/edit/", views.user_edit, name="user_edit"),
    path(
        "users/<int:pk>/password/",
        views.user_password,
        name="user_password",
    ),
]
