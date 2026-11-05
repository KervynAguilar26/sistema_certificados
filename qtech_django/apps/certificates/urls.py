"""URLs públicas del sistema de certificados."""

from django.urls import path

from . import views

app_name = "certificates"

urlpatterns = [
    path("", views.verify, name="verify"),
]
