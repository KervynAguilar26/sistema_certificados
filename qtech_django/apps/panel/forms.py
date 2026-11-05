"""Formularios del panel operativo.

Los formularios reutilizan las reglas de validación del sistema de certificados
y de usuarios, pero adaptan etiquetas y estilos a Bootstrap 5.
"""

from __future__ import annotations

from django import forms
from django.contrib.auth.forms import SetPasswordForm
from django.utils import translation

from apps.accounts.forms import (
    QTechAdminAuthenticationForm,
    UserAdminChangeForm,
    UserAdminCreationForm,
)
from apps.accounts.models import User
from apps.certificates.forms import CertificateAdminForm
from apps.core.i18n import normalize_lang, tr_admin


def _lang() -> str:
    return normalize_lang(translation.get_language(), admin=True)


def _apply_bootstrap(field: forms.Field) -> None:
    """Aplica clases de Bootstrap al widget de un campo."""

    widget = field.widget
    if isinstance(widget, forms.CheckboxInput):
        widget.attrs.setdefault("class", "form-check-input")
    elif isinstance(widget, (forms.Select, forms.SelectMultiple)):
        widget.attrs.setdefault("class", "form-select")
    elif isinstance(widget, forms.ClearableFileInput):
        widget.attrs.setdefault("class", "form-control")
    else:
        widget.attrs.setdefault("class", "form-control")


class PanelAuthenticationForm(QTechAdminAuthenticationForm):
    """Acceso al panel con estilos Bootstrap."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update(
            {
                "class": "form-control form-control-lg",
                "placeholder": "name@company.com",
            }
        )
        self.fields["password"].widget.attrs.update(
            {"class": "form-control form-control-lg"}
        )


class PanelCertificateForm(CertificateAdminForm):
    """Formulario de certificado para el panel operativo."""

    LABELS = {
        "code": "panel_field_code",
        "certificate_type": "panel_field_type",
        "applicant": "panel_field_applicant",
        "manufacturer": "panel_field_manufacturer",
        "manufacturer_address": "panel_field_manufacturer_address",
        "product": "panel_field_product",
        "brand": "panel_field_brand",
        "product_description": "panel_field_product_description",
        "models_text": "panel_field_models",
        "models_csv": "panel_field_models_csv",
        "test_parameters": "panel_field_test_parameters",
        "show_parameters": "panel_field_show_parameters",
        "test_standards": "panel_field_test_standards",
        "test_report": "panel_field_test_report",
        "issue_date": "panel_field_issue_date",
        "expiry_date": "panel_field_expiry_date",
        "status": "panel_field_status",
        "template": "panel_field_template",
    }

    HELP = {
        "code": "admin_code_help",
        "applicant": "admin_applicant_help",
        "manufacturer": "admin_manufacturer_help",
        "manufacturer_address": "admin_address_help",
        "product": "admin_product_help",
        "brand": "admin_brand_help",
        "product_description": "admin_description_help",
        "models_text": "admin_models_text_help",
        "models_csv": "admin_models_csv_help",
        "test_parameters": "admin_parameters_help",
        "show_parameters": "admin_show_parameters_help",
        "test_standards": "admin_standards_help",
        "test_report": "admin_report_help",
        "issue_date": "admin_issue_help",
        "expiry_date": "admin_expiry_help",
        "status": "admin_certificate_status_help",
        "template": "admin_default_template",
    }

    class Meta(CertificateAdminForm.Meta):
        fields = (
            "code",
            "certificate_type",
            "applicant",
            "manufacturer",
            "manufacturer_address",
            "product",
            "brand",
            "product_description",
            "models_text",
            "models_csv",
            "test_parameters",
            "show_parameters",
            "test_standards",
            "test_report",
            "issue_date",
            "expiry_date",
            "status",
            "template",
        )
        widgets = {
            "issue_date": forms.DateInput(attrs={"type": "date"}),
            "expiry_date": forms.DateInput(attrs={"type": "date"}),
            "manufacturer_address": forms.Textarea(attrs={"rows": 2}),
            "product_description": forms.Textarea(attrs={"rows": 3}),
            "models_text": forms.Textarea(attrs={"rows": 3}),
            "test_parameters": forms.Textarea(attrs={"rows": 3}),
            "test_standards": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        lang = _lang()
        for name, field in self.fields.items():
            _apply_bootstrap(field)
            label_key = self.LABELS.get(name)
            if label_key:
                field.label = tr_admin(label_key, lang)
            help_key = self.HELP.get(name)
            if help_key:
                field.help_text = tr_admin(help_key, lang)
        self.fields["certificate_type"].empty_label = tr_admin(
            "panel_field_type_empty", lang
        )
        self.fields["template"].empty_label = tr_admin(
            "panel_field_template_empty", lang
        )


class PanelUserCreateForm(UserAdminCreationForm):
    """Alta de usuarios desde el panel."""

    class Meta(UserAdminCreationForm.Meta):
        fields = ("email", "full_name", "role", "is_active")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        lang = _lang()
        labels = {
            "email": "panel_field_email",
            "full_name": "panel_field_full_name",
            "role": "panel_field_role",
            "is_active": "panel_field_active",
            "password1": "panel_field_password",
            "password2": "panel_field_password_confirm",
        }
        for name, field in self.fields.items():
            _apply_bootstrap(field)
            key = labels.get(name)
            if key:
                field.label = tr_admin(key, lang)
        self.fields["role"].choices = [
            (User.Role.ANALYST, tr_admin("panel_role_analyst", lang)),
            (User.Role.SUPERADMIN, tr_admin("panel_role_superadmin", lang)),
        ]
        self.fields["password1"].help_text = tr_admin("panel_password_help", lang)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_staff = True
        if commit:
            user.save()
        return user


class PanelUserEditForm(UserAdminChangeForm):
    """Edición de datos de un usuario."""

    class Meta(UserAdminChangeForm.Meta):
        fields = ("email", "full_name", "role", "is_active")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        lang = _lang()
        labels = {
            "email": "panel_field_email",
            "full_name": "panel_field_full_name",
            "role": "panel_field_role",
            "is_active": "panel_field_active",
        }
        for name, field in self.fields.items():
            _apply_bootstrap(field)
            key = labels.get(name)
            if key:
                field.label = tr_admin(key, lang)
        self.fields["role"].choices = [
            (User.Role.ANALYST, tr_admin("panel_role_analyst", lang)),
            (User.Role.SUPERADMIN, tr_admin("panel_role_superadmin", lang)),
        ]

    def save(self, commit=True):
        user = super().save(commit=commit)
        user.is_staff = True
        if commit:
            user.save(update_fields=["is_staff"])
        return user


class PanelPasswordForm(SetPasswordForm):
    """Cambio de contraseña de un usuario."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        lang = _lang()
        self.fields["new_password1"].label = tr_admin("panel_field_new_password", lang)
        self.fields["new_password2"].label = tr_admin(
            "panel_field_password_confirm", lang
        )
        self.fields["new_password1"].help_text = tr_admin("panel_password_help", lang)
        for field in self.fields.values():
            _apply_bootstrap(field)
