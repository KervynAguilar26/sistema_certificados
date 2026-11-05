"""Administración privada de certificados."""

from __future__ import annotations

import re

from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponse, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect
from django.urls import path, reverse
from django.utils import translation
from django.utils.html import format_html, format_html_join
from django.utils.text import slugify

from apps.core.i18n import normalize_document_lang, normalize_lang, tr_admin
from apps.core.utils import get_client_ip

from .forms import CertificateAdminForm, CertificateTemplateAdminForm
from .models import (
    Certificate,
    CertificateEvent,
    CertificateTemplate,
    CertificateTranslation,
    CertificateType,
    ValidationLog,
    generate_token,
)
from .pdf import PDFRenderError, render_certificate_pdf
from .qr import make_qr_png
from .rendering import TemplateRenderError, render_certificate_html, render_template_preview

PREVIEW_CSP = (
    "default-src 'none'; img-src data:; style-src 'unsafe-inline'; "
    "font-src data:; base-uri 'none'; form-action 'none'; frame-ancestors 'none'"
)


def _admin_lang() -> str:
    return normalize_lang(translation.get_language(), admin=True)


def _safe_filename(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", value or "certificate")
    return cleaned.strip("._") or "certificate"


class CertificateTranslationInline(admin.TabularInline):
    model = CertificateTranslation
    extra = 0
    fields = (
        "language",
        "applicant",
        "manufacturer",
        "manufacturer_address",
        "product",
        "product_description",
        "brand",
        "test_parameters",
        "test_standards",
        "test_report",
    )


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    form = CertificateAdminForm
    inlines = (CertificateTranslationInline,)
    list_display = (
        "code",
        "applicant",
        "product",
        "certificate_type",
        "expiry_date",
        "status_badge",
        "template",
        "analyst",
    )
    list_filter = (
        "status",
        "certificate_type",
        "template",
        "issue_date",
        "expiry_date",
    )
    search_fields = (
        "code",
        "applicant",
        "manufacturer",
        "product",
        "brand",
        "models_text",
        "test_report",
    )
    date_hierarchy = "issue_date"
    list_select_related = ("certificate_type", "template", "analyst")
    autocomplete_fields = ("certificate_type", "template")
    raw_id_fields = ("analyst",)
    readonly_fields = (
        "token",
        "validation_url_display",
        "qr_preview",
        "created_at",
        "updated_at",
    )
    actions = ("mark_active", "mark_blocked", "regenerate_tokens")
    list_per_page = 25
    save_as = False

    fieldsets = (
        (
            "Datos del certificado",
            {
                "fields": (
                    "code",
                    "certificate_type",
                    "applicant",
                    "manufacturer",
                    "manufacturer_address",
                    "product",
                    "brand",
                    "product_description",
                )
            },
        ),
        (
            "Modelos",
            {
                "fields": ("models_text", "models_csv"),
                "description": "Separe los modelos con comas o saltos de línea. Puede cargar un CSV.",
            },
        ),
        (
            "Ensayos",
            {
                "fields": (
                    "test_parameters",
                    "show_parameters",
                    "test_standards",
                    "test_report",
                )
            },
        ),
        (
            "Fechas y estado",
            {
                "fields": ("issue_date", "expiry_date", "status"),
                "description": "Los certificados suspendidos aparecen como inválidos en la web pública.",
            },
        ),
        (
            "Publicación",
            {"fields": ("template", "analyst")},
        ),
        (
            "Seguridad y validación",
            {
                "fields": ("token", "validation_url_display", "qr_preview"),
                "classes": ("collapse",),
            },
        ),
        (
            "Fechas del sistema",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    # ------------------------------------------------------------------
    # Acciones
    # ------------------------------------------------------------------
    def get_actions(self, request):
        actions = super().get_actions(request)
        lang = _admin_lang()
        labels = {
            "mark_active": tr_admin("admin_status_active", lang),
            "mark_blocked": tr_admin("admin_status_blocked", lang),
            "regenerate_tokens": tr_admin("admin_regenerate_token", lang),
        }
        for name, label in labels.items():
            if name in actions:
                func, action_name, _ = actions[name]
                actions[name] = (func, action_name, label)
        return actions

    @admin.action(description="Marcar como vigente")
    def mark_active(self, request, queryset):
        for certificate in queryset:
            certificate.status = Certificate.Status.ACTIVE
            certificate.save(update_fields=["status", "updated_at"])
            self._event(request, certificate, CertificateEvent.Event.STATUS_CHANGED)

    @admin.action(description="Suspender certificados")
    def mark_blocked(self, request, queryset):
        for certificate in queryset:
            certificate.status = Certificate.Status.BLOCKED
            certificate.save(update_fields=["status", "updated_at"])
            self._event(request, certificate, CertificateEvent.Event.STATUS_CHANGED)

    @admin.action(description="Regenerar tokens de verificación")
    def regenerate_tokens(self, request, queryset):
        for certificate in queryset:
            certificate.token = generate_token()
            certificate.save(update_fields=["token", "updated_at"])
            self._event(
                request, certificate, CertificateEvent.Event.TOKEN_REGENERATED
            )

    # ------------------------------------------------------------------
    # Columnas calculadas
    # ------------------------------------------------------------------
    @admin.display(description="Estado")
    def status_badge(self, obj):
        tone = obj.computed_status
        colors = {
            "valid": ("#dcfce7", "#166534"),
            "expired": ("#fef3c7", "#92400e"),
            "blocked": ("#fee2e2", "#991b1b"),
        }
        background, color = colors.get(tone, ("#e5e7eb", "#374151"))
        return format_html(
            '<span style="display:inline-block;padding:3px 9px;border-radius:999px;'
            'background:{};color:{};font-weight:700;font-size:11px;">{}</span>',
            background,
            color,
            obj.status_label(),
        )

    @admin.display(description="URL de validación")
    def validation_url_display(self, obj):
        if not obj.pk:
            return "—"
        return format_html(
            '<a href="{}" target="_blank" rel="noopener noreferrer">{}</a>',
            obj.validation_url,
            obj.validation_url,
        )

    @admin.display(description="Código QR")
    def qr_preview(self, obj):
        if not obj.pk:
            return "—"
        return format_html(
            '<img src="{}" alt="QR" style="width:150px;height:150px;background:#fff;'
            'padding:6px;border:1px solid #ddd;border-radius:6px;">',
            obj.qr_data_uri,
        )

    # ------------------------------------------------------------------
    # URLs personalizadas
    # ------------------------------------------------------------------
    def get_urls(self):
        urls = [
            path(
                "<int:pk>/render/<str:lang>/",
                self.admin_site.admin_view(self.render_view),
                name="certificates_certificate_render",
            ),
            path(
                "<int:pk>/pdf/<str:lang>/",
                self.admin_site.admin_view(self.pdf_view),
                name="certificates_certificate_pdf",
            ),
            path(
                "<int:pk>/qr/",
                self.admin_site.admin_view(self.qr_view),
                name="certificates_certificate_qr",
            ),
            path(
                "<int:pk>/regenerate-token/",
                self.admin_site.admin_view(self.regenerate_token_view),
                name="certificates_certificate_regenerate_token",
            ),
            path(
                "models-csv-template/",
                self.admin_site.admin_view(self.models_csv_template_view),
                name="certificates_certificate_models_csv_template",
            ),
        ]
        return urls + super().get_urls()

    def _get_certificate(self, request, pk: int) -> Certificate:
        certificate = get_object_or_404(Certificate, pk=pk)
        if not self.has_view_permission(request, certificate):
            raise PermissionDenied
        return certificate

    def render_view(self, request, pk: int, lang: str):
        certificate = self._get_certificate(request, pk)
        lang = normalize_document_lang(lang)
        download = request.GET.get("download") == "1"
        try:
            html = render_certificate_html(certificate, lang=lang)
        except TemplateRenderError as exc:
            messages.error(request, str(exc))
            return redirect(
                reverse("admin:certificates_certificate_change", args=[certificate.pk])
            )

        self._event(
            request,
            certificate,
            CertificateEvent.Event.DOWNLOADED
            if download
            else CertificateEvent.Event.RENDERED,
            message=lang,
        )
        response = HttpResponse(html, content_type="text/html; charset=utf-8")
        response["Content-Security-Policy"] = PREVIEW_CSP
        response["X-Content-Type-Options"] = "nosniff"
        if download:
            filename = f"certificate-{_safe_filename(certificate.code)}-{lang}.html"
            response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response

    def pdf_view(self, request, pk: int, lang: str):
        certificate = self._get_certificate(request, pk)
        lang = normalize_document_lang(lang)
        download = request.GET.get("download") == "1"
        try:
            pdf = render_certificate_pdf(certificate, lang=lang)
        except (TemplateRenderError, PDFRenderError) as exc:
            messages.error(request, str(exc))
            return redirect(
                reverse("admin:certificates_certificate_change", args=[certificate.pk])
            )

        self._event(
            request,
            certificate,
            CertificateEvent.Event.PDF_DOWNLOADED,
            message=lang,
        )
        filename = f"certificate-{_safe_filename(certificate.code)}-{lang}.pdf"
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = (
            f'{"attachment" if download else "inline"}; filename="{filename}"'
        )
        response["Cache-Control"] = "private, no-store"
        return response

    def models_csv_template_view(self, request):
        """Descarga una plantilla CSV de ejemplo para cargar modelos."""

        if not self.has_add_permission(request):
            raise PermissionDenied
        content = "Modelos\nMODELO-001\nMODELO-002\nMODELO-003\n"
        response = HttpResponse(content, content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = 'attachment; filename="plantilla_modelos.csv"'
        return response

    def qr_view(self, request, pk: int):
        certificate = self._get_certificate(request, pk)
        png = make_qr_png(certificate.validation_url)
        response = HttpResponse(png, content_type="image/png")
        if request.GET.get("download") == "1":
            filename = f"qr-{_safe_filename(certificate.code)}.png"
            response["Content-Disposition"] = f'attachment; filename="{filename}"'
        response["Cache-Control"] = "private, max-age=300"
        return response

    def regenerate_token_view(self, request, pk: int):
        if request.method != "POST":
            return HttpResponseNotAllowed(["POST"])
        certificate = get_object_or_404(Certificate, pk=pk)
        if not self.has_change_permission(request, certificate):
            raise PermissionDenied
        certificate.token = generate_token()
        certificate.save(update_fields=["token", "updated_at"])
        self._event(
            request, certificate, CertificateEvent.Event.TOKEN_REGENERATED
        )
        messages.success(request, tr_admin("admin_regenerate_token", _admin_lang()))
        return redirect(
            reverse("admin:certificates_certificate_change", args=[certificate.pk])
        )

    # ------------------------------------------------------------------
    # Guardado y auditoría
    # ------------------------------------------------------------------
    def _event(self, request, certificate, event, message=""):
        CertificateEvent.objects.create(
            certificate=certificate,
            user=request.user if request.user.is_authenticated else None,
            event=event,
            message=(message or "")[:300],
            ip_address=get_client_ip(request),
        )

    def save_model(self, request, obj, form, change):
        if not obj.analyst_id:
            obj.analyst = request.user
        super().save_model(request, obj, form, change)
        event = CertificateEvent.Event.UPDATED if change else CertificateEvent.Event.CREATED
        if change and "status" in form.changed_data:
            event = CertificateEvent.Event.STATUS_CHANGED
        self._event(request, obj, event)

    def get_readonly_fields(self, request, obj=None):
        return self.readonly_fields


@admin.register(CertificateType)
class CertificateTypeAdmin(admin.ModelAdmin):
    list_display = ("name_es", "name_en", "name_zh", "is_default")
    list_editable = ("is_default",)
    search_fields = ("name_es", "name_en", "name_zh")
    ordering = ("name_es",)


@admin.register(CertificateTemplate)
class CertificateTemplateAdmin(admin.ModelAdmin):
    form = CertificateTemplateAdminForm
    list_display = ("name", "is_default", "updated_at", "preview_column")
    list_filter = ("is_default",)
    search_fields = ("name", "description")
    readonly_fields = (
        "placeholders_help",
        "preview_column",
        "created_at",
        "updated_at",
    )
    fieldsets = (
        (
            "Plantilla",
            {"fields": ("name", "description", "is_default")},
        ),
        (
            "Código y archivo",
            {
                "fields": ("file", "content"),
                "description": (
                    "Suba un archivo .html (máx. 1 MB) o pegue el código. "
                    "Si sube un archivo, su contenido reemplaza el código."
                ),
            },
        ),
        (
            "Imagen de fondo",
            {
                "fields": ("background_image",),
                "description": (
                    "Opcional. Recomendado 1240 x 1754 px (A4 a 150 ppp), PNG o JPG."
                ),
            },
        ),
        (
            "Ayuda y vista previa",
            {
                "fields": ("placeholders_help", "preview_column"),
            },
        ),
        (
            "Fechas",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def get_urls(self):
        urls = [
            path(
                "<int:pk>/preview/<str:lang>/",
                self.admin_site.admin_view(self.preview_view),
                name="certificates_certificatetemplate_preview",
            ),
        ]
        return urls + super().get_urls()

    def preview_view(self, request, pk: int, lang: str):
        template = get_object_or_404(CertificateTemplate, pk=pk)
        if not self.has_view_permission(request, template):
            raise PermissionDenied
        lang = normalize_document_lang(lang)
        try:
            html = render_template_preview(template, lang=lang)
        except TemplateRenderError as exc:
            messages.error(request, str(exc))
            return redirect(
                reverse(
                    "admin:certificates_certificatetemplate_change",
                    args=[template.pk],
                )
            )
        response = HttpResponse(html, content_type="text/html; charset=utf-8")
        response["Content-Security-Policy"] = PREVIEW_CSP
        response["X-Content-Type-Options"] = "nosniff"
        return response

    @admin.display(description="Vista previa")
    def preview_column(self, obj):
        if not obj.pk:
            return "—"
        lang = _admin_lang()
        en_url = reverse(
            "admin:certificates_certificatetemplate_preview", args=[obj.pk, "en"]
        )
        es_url = reverse(
            "admin:certificates_certificatetemplate_preview", args=[obj.pk, "es"]
        )
        zh_url = reverse(
            "admin:certificates_certificatetemplate_preview", args=[obj.pk, "zh-hans"]
        )
        return format_html(
            '<a class="button" href="{}" target="_blank" rel="noopener">English</a> '
            '<a class="button" href="{}" target="_blank" rel="noopener">Español</a> '
            '<a class="button" href="{}" target="_blank" rel="noopener">中文</a>',
            en_url,
            es_url,
            zh_url,
        )

    @admin.display(description="Marcadores disponibles")
    def placeholders_help(self, obj):
        placeholders = [
            "code",
            "certificate_type",
            "applicant",
            "manufacturer",
            "manufacturer_address",
            "product",
            "product_description",
            "brand",
            "models",
            "models_text",
            "models_display",
            "models_count",
            "test_parameters",
            "test_standards",
            "test_report",
            "issue_date",
            "expiry_date",
            "status",
            "status_label",
            "validation_url",
            "qr_code",
            "logo",
            "background",
            "site",
            "t",
            "page_count",
            "annex_pages",
            "generated_at",
        ]
        tags = "{% if %} · {% for %} · {% with %} · {% comment %}"
        filters = "default · date · join · linebreaksbr · upper · lower · length"
        items = format_html_join(
            "",
            "<li><code>{{{{ {} }}}}</code></li>",
            ((name,) for name in placeholders),
        )
        return format_html(
            '<div class="help"><p><strong>Etiquetas permitidas:</strong> {}</p>'
            "<p><strong>Filtros permitidos:</strong> {}</p>"
            '<ul style="columns:2;">{}</ul></div>',
            tags,
            filters,
            items,
        )


@admin.register(CertificateEvent)
class CertificateEventAdmin(admin.ModelAdmin):
    list_display = ("certificate", "event", "user", "created_at")
    list_filter = ("event", "created_at")
    search_fields = ("certificate__code", "message", "user__email")
    readonly_fields = ("certificate", "user", "event", "message", "ip_address", "created_at")
    date_hierarchy = "created_at"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ValidationLog)
class ValidationLogAdmin(admin.ModelAdmin):
    list_display = ("query", "result", "success", "certificate", "ip_address", "created_at")
    list_filter = ("result", "success", "created_at")
    search_fields = ("query", "certificate__code", "ip_address")
    readonly_fields = (
        "certificate",
        "query",
        "result",
        "success",
        "ip_address",
        "user_agent",
        "created_at",
    )
    date_hierarchy = "created_at"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
