"""Formularios del sistema de certificados (etiquetas en español)."""

from __future__ import annotations

import csv
import io
from datetime import timedelta

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import Certificate, CertificateTemplate, CertificateTranslation, _split_models
from .security import MAX_TEMPLATE_BYTES, validate_certificate_template, validate_template_file


class CertificateAdminForm(forms.ModelForm):
    models_csv = forms.FileField(
        label="Cargar modelos desde CSV",
        required=False,
        help_text="Archivo CSV con un modelo por línea. Reemplaza la lista actual.",
        widget=forms.ClearableFileInput(attrs={"accept": ".csv,text/csv"}),
    )

    class Meta:
        model = Certificate
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        today = timezone.localdate()
        if not self.is_bound:
            if not self.initial.get("issue_date"):
                self.initial["issue_date"] = today
            if not self.initial.get("expiry_date"):
                self.initial["expiry_date"] = today + timedelta(days=365 * 3)
            if not self.initial.get("certificate_type"):
                from .models import CertificateType

                default_type = CertificateType.objects.filter(is_default=True).first()
                if default_type:
                    self.initial["certificate_type"] = default_type.pk
            if not self.initial.get("template"):
                default_template = CertificateTemplate.objects.filter(
                    is_default=True
                ).first()
                if default_template:
                    self.initial["template"] = default_template.pk

    def clean_models_csv(self):
        uploaded = self.cleaned_data.get("models_csv")
        if not uploaded:
            return uploaded
        if uploaded.size > 5 * 1024 * 1024:
            raise ValidationError("El archivo CSV no puede superar 5 MB.")
        raw = uploaded.read()
        try:
            text = raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            text = raw.decode("latin-1", errors="replace")

        models: list[str] = []
        try:
            reader = csv.reader(io.StringIO(text))
            for row in reader:
                if row and row[0].strip():
                    models.extend(_split_models(row[0]))
        except csv.Error as exc:
            raise ValidationError("No se pudo leer el archivo CSV.") from exc

        if not models:
            raise ValidationError("El archivo CSV no contiene modelos válidos.")
        # Deduplicar conservando el orden. El valor se aplica en clean() para
        # garantizar que sobrescribe el campo models_text ya validado.
        unique: list[str] = []
        seen: set[str] = set()
        for model in models:
            key = model.casefold()
            if key not in seen:
                seen.add(key)
                unique.append(model)
        self._csv_models = unique
        return uploaded

    def clean(self):
        cleaned = super().clean()
        csv_models = getattr(self, "_csv_models", None)
        if csv_models:
            cleaned["models_text"] = ", ".join(csv_models)
        return cleaned

    def clean_code(self):
        code = (self.cleaned_data.get("code") or "").strip()
        if not code:
            raise ValidationError("El número de certificado es obligatorio.")
        return code


class CertificateTemplateAdminForm(forms.ModelForm):
    class Meta:
        model = CertificateTemplate
        fields = "__all__"

    def clean(self):
        cleaned = super().clean()
        uploaded = cleaned.get("file")
        content = (cleaned.get("content") or "").strip()

        if uploaded:
            try:
                content = validate_template_file(uploaded)
            except ValidationError as exc:
                raise ValidationError({"file": exc.messages}) from exc
            # validate_template_file() consume el archivo; vuelve al inicio
            # para que Django pueda guardarlo correctamente.
            uploaded.seek(0)
        elif content:
            try:
                validate_certificate_template(content)
            except ValidationError as exc:
                raise ValidationError({"content": exc.messages}) from exc
        else:
            raise ValidationError(
                {"file": "Suba un archivo HTML o pegue el código de la plantilla."}
            )

        if len(content.encode("utf-8")) > MAX_TEMPLATE_BYTES:
            raise ValidationError({"file": "La plantilla supera el tamaño máximo de 1 MB."})
        cleaned["content"] = content
        return cleaned


class CertificateTranslationForm(forms.ModelForm):
    class Meta:
        model = CertificateTranslation
        fields = "__all__"
