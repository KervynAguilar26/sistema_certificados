"""Administración de usuarios."""

from __future__ import annotations

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils import translation

from apps.core.i18n import normalize_lang, tr_admin

from .forms import UserAdminChangeForm, UserAdminCreationForm
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    form = UserAdminChangeForm
    add_form = UserAdminCreationForm
    model = User

    list_display = (
        "email",
        "full_name",
        "role_label",
        "is_active",
        "is_staff",
        "last_login",
    )
    list_filter = ("role", "is_active", "is_staff")
    search_fields = ("email", "full_name")
    ordering = ("email",)
    readonly_fields = ("last_login", "date_joined")

    fieldsets = (
        (
            "Datos de acceso",
            {"fields": ("email", "password")},
        ),
        (
            "Datos personales",
            {"fields": ("full_name", "role")},
        ),
        (
            "Permisos",
            {
                "fields": ("is_active", "is_staff", "is_superuser"),
                "classes": ("collapse",),
            },
        ),
        (
            "Fechas",
            {"fields": ("last_login", "date_joined"), "classes": ("collapse",)},
        ),
    )

    add_fieldsets = (
        (
            "Nuevo usuario",
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "full_name",
                    "role",
                    "password1",
                    "password2",
                    "is_active",
                    "is_staff",
                ),
            },
        ),
    )

    actions = ("activate_users", "deactivate_users")

    def get_actions(self, request):
        actions = super().get_actions(request)
        lang = normalize_lang(translation.get_language(), admin=True)
        labels = {
            "activate_users": tr_admin("admin_active", lang),
            "deactivate_users": tr_admin("admin_inactive", lang),
        }
        for name, label in labels.items():
            if name in actions:
                func, action_name, _ = actions[name]
                actions[name] = (func, action_name, label)
        return actions

    @admin.action(description="Activar usuarios")
    def activate_users(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description="Desactivar usuarios")
    def deactivate_users(self, request, queryset):
        queryset.exclude(pk=request.user.pk).update(is_active=False)

    # Solo el superadministrador puede gestionar cuentas.
    def has_module_permission(self, request):
        return bool(request.user.is_active and request.user.is_superadmin)

    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_add_permission(self, request):
        return self.has_module_permission(request)

    def has_change_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_delete_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def save_model(self, request, obj, form, change):
        # Un superadministrador siempre debe tener acceso al panel.
        if obj.role == User.Role.SUPERADMIN:
            obj.is_staff = True
        super().save_model(request, obj, form, change)
