"""Modelos del sistema privado de certificados."""

from __future__ import annotations

import re
import secrets

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.storage import storages
from django.core.validators import FileExtensionValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone

from apps.core.i18n import normalize_document_lang, tr

from .qr import make_qr_data_uri
from .security import validate_certificate_template

private_storage = storages["private"]


def generate_token() -> str:
    return secrets.token_hex(32)


def _split_models(value: str) -> list[str]:
    if not value:
        return []
    normalized = (
        value.replace("<br />", "\n")
        .replace("<br/>", "\n")
        .replace("<br>", "\n")
    )
    parts = re.split(r"[,;\n\r]+", normalized)
    seen: set[str] = set()
    models: list[str] = []
    for part in parts:
        model = part.strip()
        if not model:
            continue
        if model.lower() in {"modelo", "modelos"}:
            continue
        key = model.casefold()
        if key in seen:
            continue
        seen.add(key)
        models.append(model)
    return models


class CertificateType(models.Model):
    name_es = models.CharField("Nombre en español", max_length=150)
    name_en = models.CharField("Nombre en inglés", max_length=150, blank=True)
    name_zh = models.CharField("Nombre en chino", max_length=150, blank=True)
    is_default = models.BooleanField("Tipo predeterminado", default=False)

    class Meta:
        verbose_name = "Tipo de certificado"
        verbose_name_plural = "Tipos de certificado"
        ordering = ("name_es",)

    def __str__(self) -> str:
        return self.name_es

    def label(self, lang: str | None = None) -> str:
        lang = normalize_document_lang(lang)
        if lang == "en":
            return self.name_en or self.name_es
        if lang == "zh-hans":
            return self.name_zh or self.name_en or self.name_es
        return self.name_es

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.is_default:
            CertificateType.objects.exclude(pk=self.pk).update(is_default=False)


class CertificateTemplate(models.Model):
    name = models.CharField("Nombre", max_length=150)
    description = models.TextField("Descripción", blank=True)
    file = models.FileField(
        "Archivo HTML",
        upload_to="certificate_templates/",
        storage=private_storage,
        blank=True,
        validators=[FileExtensionValidator(["html", "htm"])],
        help_text="Archivo .html de máximo 1 MB.",
    )
    content = models.TextField(
        "Código HTML",
        blank=True,
        help_text="Plantilla HTML con marcadores como {{ code }} o {{ product }}.",
    )
    background_image = models.ImageField(
        "Imagen de fondo",
        upload_to="certificate_templates/backgrounds/",
        storage=private_storage,
        blank=True,
        help_text="Opcional. Recomendado 1240 x 1754 px (A4 a 150 ppp).",
    )
    is_default = models.BooleanField("Plantilla predeterminada", default=False)
    created_at = models.DateTimeField("Creado el", auto_now_add=True)
    updated_at = models.DateTimeField("Actualizado el", auto_now=True)

    class Meta:
        verbose_name = "Plantilla de certificado"
        verbose_name_plural = "Plantillas de certificado"
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name

    def clean(self):
        super().clean()
        if self.content:
            validate_certificate_template(self.content)
        elif not self.file:
            raise ValidationError(
                "Suba un archivo HTML o pegue el código de la plantilla."
            )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.is_default:
            CertificateTemplate.objects.exclude(pk=self.pk).update(is_default=False)

    @property
    def background_data_uri(self) -> str:
        if not self.background_image:
            return ""
        from apps.core.templatetags.qtech_tags import data_uri

        return data_uri(self.background_image)


class Certificate(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "activo", "Activo"
        BLOCKED = "bloqueado", "Bloqueado"

    code = models.CharField(
        "N.º de certificado",
        max_length=100,
        unique=True,
        help_text="Número único impreso en el certificado.",
    )
    certificate_type = models.ForeignKey(
        CertificateType,
        verbose_name="Tipo de certificado",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="certificates",
    )
    token = models.CharField(
        "Token de verificación",
        max_length=128,
        unique=True,
        default=generate_token,
        editable=False,
    )

    applicant = models.CharField("Solicitante", max_length=200)
    manufacturer = models.CharField("Fabricante", max_length=200, blank=True)
    manufacturer_address = models.TextField("Dirección del fabricante", blank=True)
    product = models.CharField("Producto", max_length=200)
    product_description = models.TextField("Descripción del producto", blank=True)
    brand = models.CharField("Marca", max_length=200, blank=True)
    models_text = models.TextField(
        "Modelos",
        blank=True,
        help_text="Separe los modelos con comas o saltos de línea.",
    )

    test_parameters = models.TextField("Parámetros de ensayo", blank=True)
    show_parameters = models.BooleanField("Mostrar parámetros", default=True)
    test_standards = models.TextField("Normas de ensayo", blank=True)
    test_report = models.CharField("Informe de ensayo", max_length=150, blank=True)

    issue_date = models.DateField("Fecha de emisión", default=timezone.localdate)
    expiry_date = models.DateField("Fecha de vencimiento")
    status = models.CharField(
        "Estado",
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )

    template = models.ForeignKey(
        CertificateTemplate,
        verbose_name="Plantilla",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="certificates",
        help_text="Si se deja vacío se usa la plantilla predeterminada.",
    )
    analyst = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Analista",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="certificates",
    )

    created_at = models.DateTimeField("Creado el", auto_now_add=True)
    updated_at = models.DateTimeField("Actualizado el", auto_now=True)

    class Meta:
        verbose_name = "Certificado"
        verbose_name_plural = "Certificados"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["code"]),
            models.Index(fields=["token"]),
            models.Index(fields=["status", "expiry_date"]),
        ]

    def __str__(self) -> str:
        return self.code

    def clean(self):
        super().clean()
        self.code = (self.code or "").strip()
        if not self.code:
            raise ValidationError({"code": "El número de certificado es obligatorio."})
        if self.issue_date and self.expiry_date and self.expiry_date < self.issue_date:
            raise ValidationError(
                {"expiry_date": "La fecha de vencimiento no puede ser anterior a la emisión."}
            )

    def save(self, *args, **kwargs):
        self.code = (self.code or "").strip()
        if not self.token:
            self.token = generate_token()
        super().save(*args, **kwargs)

    # ------------------------------------------------------------------
    # Datos derivados
    # ------------------------------------------------------------------
    @property
    def models_list(self) -> list[str]:
        return _split_models(self.models_text)

    @property
    def models_count(self) -> int:
        return len(self.models_list)

    @property
    def has_annex(self) -> bool:
        return self.models_count > 10

    @property
    def is_expired(self) -> bool:
        return bool(self.expiry_date and self.expiry_date < timezone.localdate())

    @property
    def computed_status(self) -> str:
        if self.status == self.Status.BLOCKED:
            return "blocked"
        if self.is_expired:
            return "expired"
        return "valid"

    def status_label(self, lang: str | None = None) -> str:
        return tr(f"status_{self.computed_status}", lang=normalize_document_lang(lang))

    @property
    def validation_url(self) -> str:
        base = settings.SITE_BASE_URL.rstrip("/")
        return f"{base}{reverse('certificates:verify')}?token={self.token}"

    @property
    def validation_url_by_code(self) -> str:
        base = settings.SITE_BASE_URL.rstrip("/")
        return f"{base}{reverse('certificates:verify')}?q={self.code}"

    @property
    def qr_data_uri(self) -> str:
        return make_qr_data_uri(self.validation_url)

    def type_label(self, lang: str | None = None) -> str:
        lang = normalize_document_lang(lang)
        if self.certificate_type_id:
            return self.certificate_type.label(lang)
        return tr("cert_title", lang=lang)

    def data_for_language(self, lang: str | None = None) -> dict:
        """Devuelve los campos traducidos del certificado con respaldo al original."""

        lang = normalize_document_lang(lang)
        translation = None
        if self.pk:
            translation = self.translations.filter(language=lang).first()

        def pick(field: str) -> str:
            if translation:
                value = (getattr(translation, field, "") or "").strip()
                if value:
                    return value
            return getattr(self, field, "") or ""

        return {
            "applicant": pick("applicant"),
            "manufacturer": pick("manufacturer"),
            "manufacturer_address": pick("manufacturer_address"),
            "product": pick("product"),
            "product_description": pick("product_description"),
            "brand": pick("brand"),
            "test_parameters": pick("test_parameters"),
            "test_standards": pick("test_standards"),
            "test_report": pick("test_report"),
        }

    def models_display(self, lang: str | None = None) -> str:
        lang = normalize_document_lang(lang)
        if self.has_annex:
            return tr("cert_see_annex", lang=lang)
        return ", ".join(self.models_list) or tr("cert_no_models", lang=lang)


class CertificateTranslation(models.Model):
    class Language(models.TextChoices):
        EN = "en", "Inglés"
        ZH = "zh-hans", "Chino"

    certificate = models.ForeignKey(
        Certificate,
        verbose_name="Certificado",
        on_delete=models.CASCADE,
        related_name="translations",
    )
    language = models.CharField(
        "Idioma",
        max_length=10,
        choices=Language.choices,
    )
    applicant = models.CharField("Solicitante", max_length=200, blank=True)
    manufacturer = models.CharField("Fabricante", max_length=200, blank=True)
    manufacturer_address = models.TextField("Dirección del fabricante", blank=True)
    product = models.CharField("Producto", max_length=200, blank=True)
    product_description = models.TextField("Descripción del producto", blank=True)
    brand = models.CharField("Marca", max_length=200, blank=True)
    test_parameters = models.TextField("Parámetros de ensayo", blank=True)
    test_standards = models.TextField("Normas de ensayo", blank=True)
    test_report = models.CharField("Informe de ensayo", max_length=150, blank=True)

    class Meta:
        verbose_name = "Traducción del certificado"
        verbose_name_plural = "Traducciones del certificado"
        constraints = [
            models.UniqueConstraint(
                fields=("certificate", "language"),
                name="unique_certificate_language",
            )
        ]
        ordering = ("certificate", "language")

    def __str__(self) -> str:
        return f"{self.certificate.code} · {self.get_language_display()}"


class CertificateEvent(models.Model):
    class Event(models.TextChoices):
        CREATED = "created", "Creado"
        UPDATED = "updated", "Actualizado"
        STATUS_CHANGED = "status_changed", "Cambio de estado"
        TOKEN_REGENERATED = "token_regenerated", "Token regenerado"
        RENDERED = "rendered", "Vista previa HTML"
        DOWNLOADED = "downloaded", "HTML descargado"
        PDF_DOWNLOADED = "pdf_downloaded", "PDF descargado"

    certificate = models.ForeignKey(
        Certificate,
        verbose_name="Certificado",
        on_delete=models.CASCADE,
        related_name="events",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Usuario",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="certificate_events",
    )
    event = models.CharField("Evento", max_length=30, choices=Event.choices)
    message = models.CharField("Detalle", max_length=300, blank=True)
    ip_address = models.GenericIPAddressField("Dirección IP", null=True, blank=True)
    created_at = models.DateTimeField("Fecha", default=timezone.now)

    class Meta:
        verbose_name = "Evento de certificado"
        verbose_name_plural = "Eventos de certificado"
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.certificate.code} · {self.get_event_display()}"


class ValidationLog(models.Model):
    class Result(models.TextChoices):
        VALID = "valid", "Vigente"
        EXPIRED = "expired", "Vencido"
        BLOCKED = "blocked", "Suspendido"
        NOT_FOUND = "not_found", "No encontrado"
        RATE_LIMITED = "rate_limited", "Limitado"

    certificate = models.ForeignKey(
        Certificate,
        verbose_name="Certificado",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="validations",
    )
    query = models.CharField("Consulta", max_length=200, blank=True)
    result = models.CharField("Resultado", max_length=20, choices=Result.choices)
    success = models.BooleanField("Encontrado", default=False)
    ip_address = models.GenericIPAddressField("Dirección IP", null=True, blank=True)
    user_agent = models.CharField("Navegador", max_length=300, blank=True)
    created_at = models.DateTimeField("Fecha", default=timezone.now)

    class Meta:
        verbose_name = "Intento de validación"
        verbose_name_plural = "Intentos de validación"
        ordering = ("-created_at",)
        indexes = [models.Index(fields=["-created_at"])]

    def __str__(self) -> str:
        return f"{self.query or '—'} · {self.get_result_display()}"
