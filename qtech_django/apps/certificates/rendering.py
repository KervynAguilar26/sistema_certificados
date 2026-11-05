"""Renderizado seguro de certificados HTML."""

from __future__ import annotations

import base64
import mimetypes
from datetime import timedelta
from pathlib import Path

from django.contrib.staticfiles import finders
from django.core.exceptions import ValidationError
from django.template import Context, Template, TemplateSyntaxError
from django.utils import timezone

from apps.core.i18n import LazyTr, normalize_document_lang, tr
from apps.core.models import SiteSettings

from .models import Certificate, CertificateTemplate
from .security import validate_certificate_template

MODELS_PER_ANNEX_PAGE = 180


class TemplateRenderError(Exception):
    """Error controlado al compilar o renderizar una plantilla."""


def default_template_source() -> str:
    path = (
        Path(__file__).resolve().parent
        / "templates"
        / "certificates"
        / "default_certificate.html"
    )
    return path.read_text(encoding="utf-8")


def _static_data_uri(path: str) -> str:
    found = finders.find(path)
    if not found:
        return ""
    file_path = Path(found)
    try:
        raw = file_path.read_bytes()
    except OSError:
        return ""
    mime = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
    return f"data:{mime};base64,{base64.b64encode(raw).decode('ascii')}"


def _field_data_uri(field) -> str:
    if not field:
        return ""
    try:
        field.open("rb")
        raw = field.read()
        name = getattr(field, "name", "") or ""
    except Exception:
        return ""
    finally:
        try:
            field.close()
        except Exception:
            pass
    mime = mimetypes.guess_type(name)[0] or "application/octet-stream"
    return f"data:{mime};base64,{base64.b64encode(raw).decode('ascii')}"


def _resolve_template(certificate: Certificate) -> CertificateTemplate | None:
    if certificate.template_id:
        return certificate.template
    return CertificateTemplate.objects.filter(is_default=True).first()


def _background_for(template: CertificateTemplate | None) -> str:
    if template and template.background_image:
        return _field_data_uri(template.background_image)
    # La plantilla incluida conserva el marco dorado original del sistema PHP.
    return _static_data_uri("img/marco_dorado.png")


def _annex_background_for(template: CertificateTemplate | None) -> str:
    """Fondo de las páginas de anexo.

    Las plantillas personalizadas usan su propia imagen; la plantilla incluida
    conserva el segundo marco dorado del sistema anterior.
    """

    if template and template.background_image:
        return _field_data_uri(template.background_image)
    return _static_data_uri("img/marco_dorado 2.png")


def build_certificate_context(
    certificate: Certificate,
    lang: str = "en",
    template: CertificateTemplate | None = None,
) -> dict:
    # Los certificados son documentos y se pueden emitir en chino, inglés o
    # español, independientemente del idioma de la web pública y del panel.
    lang = normalize_document_lang(lang)
    data = certificate.data_for_language(lang)
    site = SiteSettings.load()
    t = LazyTr(lang)

    models = certificate.models_list
    annex_pages: list[dict] = []
    if len(models) > 10:
        for index in range(0, len(models), MODELS_PER_ANNEX_PAGE):
            chunk = models[index : index + MODELS_PER_ANNEX_PAGE]
            annex_pages.append(
                {
                    "number": len(annex_pages) + 2,
                    "models": chunk,
                    "models_text": ", ".join(chunk),
                }
            )

    total_pages = 1 + len(annex_pages)
    logo = _field_data_uri(site.logo) or _static_data_uri("img/logo.png")
    background = _background_for(template)
    background_annex = _annex_background_for(template)
    qr_code = certificate.qr_data_uri

    context = {
        "certificate": certificate,
        "cert": certificate,
        "code": certificate.code,
        "certificate_type": certificate.type_label(lang),
        "applicant": data["applicant"],
        "manufacturer": data["manufacturer"],
        "manufacturer_address": data["manufacturer_address"],
        "product": data["product"],
        "product_description": data["product_description"],
        "brand": data["brand"],
        "models": models,
        "models_text": certificate.models_text,
        "models_display": certificate.models_display(lang),
        "models_count": len(models),
        "model_count": len(models),
        "has_annex": bool(annex_pages),
        "annex_pages": annex_pages,
        "annex_count": len(annex_pages),
        "test_parameters": data["test_parameters"],
        "show_parameters": bool(certificate.show_parameters and data["test_parameters"]),
        "test_standards": data["test_standards"],
        "test_report": data["test_report"],
        "issue_date": certificate.issue_date.strftime("%d/%m/%Y")
        if certificate.issue_date
        else "",
        "issue_date_iso": certificate.issue_date.isoformat()
        if certificate.issue_date
        else "",
        "expiry_date": certificate.expiry_date.strftime("%d/%m/%Y")
        if certificate.expiry_date
        else "",
        "expiry_date_iso": certificate.expiry_date.isoformat()
        if certificate.expiry_date
        else "",
        "status": certificate.computed_status,
        "status_label": certificate.status_label(lang),
        "validation_url": certificate.validation_url,
        "qr_code": qr_code,
        "logo": logo,
        "background": background,
        "background_annex": background_annex,
        "site": site,
        "lang": lang,
        "language": lang,
        "t": t,
        "labels": t,
        "page_count": total_pages,
        "generated_at": timezone.now(),
        "year": timezone.localdate().year,
    }
    return context


def render_certificate_html(
    certificate: Certificate,
    lang: str = "en",
    template: CertificateTemplate | None = None,
) -> str:
    """Compila y renderiza la plantilla del certificado.

    Se valida el código fuente antes de compilar para impedir etiquetas y
    filtros peligrosos. La autoescape de Django permanece activa para todos los
    datos del certificado.
    """

    resolved = template or _resolve_template(certificate)
    source = resolved.content if resolved and resolved.content else default_template_source()
    try:
        validate_certificate_template(source)
    except ValidationError as exc:
        raise TemplateRenderError("; ".join(exc.messages)) from exc

    context = build_certificate_context(certificate, lang=lang, template=resolved)
    try:
        compiled = Template(source)
        return compiled.render(Context(context, autoescape=True))
    except TemplateSyntaxError as exc:
        raise TemplateRenderError(f"Error de sintaxis en la plantilla: {exc}") from exc
    except Exception as exc:  # pragma: no cover - defensa adicional
        raise TemplateRenderError(f"No se pudo renderizar la plantilla: {exc}") from exc


def sample_certificate() -> Certificate:
    """Certificado en memoria para previsualizar plantillas."""

    default_type = None
    try:
        from .models import CertificateType

        default_type = CertificateType.objects.filter(is_default=True).first()
    except Exception:
        pass
    today = timezone.localdate()
    return Certificate(
        code="SAMPLE-0001",
        certificate_type=default_type,
        applicant="Sample Trading Company",
        manufacturer="Sample Manufacturing Co., Ltd.",
        manufacturer_address="No. 1 Industrial Road, Qingdao, China",
        product="Sample product",
        product_description=(
            "This is a sample description used to preview the certificate template."
        ),
        brand="SAMPLE",
        models_text="1001, 1002, 1003, 1004, 1005",
        test_parameters="Sample test parameters",
        show_parameters=True,
        test_standards="ISO 9001:2015",
        test_report="SAMPLE-REPORT-001",
        issue_date=today,
        expiry_date=today + timedelta(days=365),
    )


def render_template_preview(template: CertificateTemplate, lang: str = "en") -> str:
    return render_certificate_html(
        sample_certificate(), lang=lang, template=template
    )
