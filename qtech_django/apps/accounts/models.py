"""Modelo de usuario con roles del sistema de certificados."""

from __future__ import annotations

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone

from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        SUPERADMIN = "superadmin", "Superadministrador"
        ANALYST = "analista", "Analista"

    email = models.EmailField("Correo electrónico", unique=True)
    full_name = models.CharField("Nombre completo", max_length=150)
    role = models.CharField(
        "Rol",
        max_length=20,
        choices=Role.choices,
        default=Role.ANALYST,
    )
    is_active = models.BooleanField("Activo", default=True)
    is_staff = models.BooleanField("Acceso al panel", default=True)
    date_joined = models.DateTimeField("Fecha de alta", default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    # Permisos que puede ejercer un analista dentro del panel. El superadmin
    # recibe todos los permisos sin necesidad de asignarlos uno a uno.
    ANALYST_PERMISSIONS = {
        "certificates.add_certificate",
        "certificates.change_certificate",
        "certificates.view_certificate",
        "certificates.view_certificatetype",
        "certificates.view_certificatetemplate",
        "certificates.view_certificateevent",
        "certificates.view_validationlog",
    }

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
        ordering = ("email",)

    def __str__(self) -> str:
        return self.email

    def get_full_name(self) -> str:
        return self.full_name or self.email

    def get_short_name(self) -> str:
        return self.full_name.split(" ", 1)[0] if self.full_name else self.email

    @property
    def is_superadmin(self) -> bool:
        return self.role == self.Role.SUPERADMIN or self.is_superuser

    @property
    def role_label(self) -> str:
        from apps.core.i18n import tr_admin

        key = "admin_superadmin" if self.is_superadmin else "admin_analyst"
        return tr_admin(key)

    def has_perm(self, perm, obj=None):
        if not self.is_active:
            return False
        if self.is_superadmin:
            return True
        if super().has_perm(perm, obj):
            return True
        if self.role == self.Role.ANALYST:
            return perm in self.ANALYST_PERMISSIONS
        return False

    def has_module_perms(self, app_label):
        if not self.is_active:
            return False
        if self.is_superadmin:
            return True
        if self.role == self.Role.ANALYST:
            return app_label == "certificates"
        return super().has_module_perms(app_label)
