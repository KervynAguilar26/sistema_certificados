"""Formularios de usuarios y de acceso al panel."""

from __future__ import annotations

from django import forms
from django.contrib.auth.forms import AuthenticationForm, ReadOnlyPasswordHashField
from django.core.exceptions import ValidationError
from django.utils import translation

from apps.core.i18n import normalize_lang, tr_admin
from apps.core.utils import get_client_ip, rate_limit, rate_limit_peek, reset_rate_limit

from .models import User


class QTechAdminAuthenticationForm(AuthenticationForm):
    """Formulario de acceso con límite de intentos por IP y por usuario."""

    username = forms.EmailField(
        label="Correo electrónico",
        widget=forms.EmailInput(
            attrs={"autofocus": True, "autocomplete": "username", "class": "vTextField"}
        ),
    )
    password = forms.CharField(
        label="Contraseña",
        strip=False,
        widget=forms.PasswordInput(
            attrs={"autocomplete": "current-password", "class": "vTextField"}
        ),
    )

    def __init__(self, request=None, *args, **kwargs):
        super().__init__(request=request, *args, **kwargs)
        lang = normalize_lang(translation.get_language(), admin=True)
        self.fields["username"].label = tr_admin("admin_login_email", lang)
        self.fields["password"].label = tr_admin("admin_login_password", lang)
        self.error_messages["invalid_login"] = tr_admin(
            "admin_login_email", lang
        )  # se reemplaza abajo con un mensaje más claro
        self.error_messages["invalid_login"] = (
            "Correo o contraseña incorrectos." if lang == "es" else
            ("邮箱或密码不正确。" if lang == "zh-hans" else "Invalid email or password.")
        )

    def _keys(self) -> tuple[str, str]:
        request = self.request
        ip = get_client_ip(request) if request is not None else "unknown"
        username = (self.data.get("username") or "").strip().lower()[:150]
        return f"admin-login-ip:{ip}", f"admin-login-user:{username}"

    def clean(self):
        lang = normalize_lang(translation.get_language(), admin=True)
        ip_key, user_key = self._keys()
        if rate_limit_peek(ip_key) >= 10 or rate_limit_peek(user_key) >= 8:
            raise ValidationError(tr_admin("admin_login_locked", lang))
        try:
            cleaned = super().clean()
        except ValidationError:
            rate_limit(ip_key, limit=10, window=15 * 60)
            rate_limit(user_key, limit=8, window=15 * 60)
            raise
        reset_rate_limit(ip_key)
        reset_rate_limit(user_key)
        return cleaned


class UserAdminCreationForm(forms.ModelForm):
    password1 = forms.CharField(
        label="Contraseña",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        help_text="Mínimo 12 caracteres, no numérica y no demasiado común.",
    )
    password2 = forms.CharField(
        label="Confirmar contraseña",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )

    class Meta:
        model = User
        fields = ("email", "full_name", "role", "is_active", "is_staff")

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError("Las contraseñas no coinciden.")
        if password2:
            from django.contrib.auth.password_validation import validate_password

            validate_password(password2)
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class UserAdminChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField(
        label="Contraseña",
        help_text=(
            "Las contraseñas no se almacenan en texto plano. Use el enlace "
            "«Cambiar contraseña» para actualizarla."
        ),
    )

    class Meta:
        model = User
        fields = (
            "email",
            "full_name",
            "role",
            "is_active",
            "is_staff",
            "is_superuser",
            "password",
        )

    def clean_password(self):
        return self.initial.get("password", "")

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()

    def clean(self):
        cleaned = super().clean()
        role = cleaned.get("role")
        is_active = cleaned.get("is_active")
        if self.instance and self.instance.pk:
            other_superadmins = User.objects.filter(
                role=User.Role.SUPERADMIN, is_active=True
            ).exclude(pk=self.instance.pk)
            losing_superadmin = (
                self.instance.role == User.Role.SUPERADMIN
                and self.instance.is_active
                and (role != User.Role.SUPERADMIN or not is_active)
            )
            if losing_superadmin and not other_superadmins.exists():
                raise ValidationError(
                    "Debe existir al menos un superadministrador activo."
                )
        return cleaned
