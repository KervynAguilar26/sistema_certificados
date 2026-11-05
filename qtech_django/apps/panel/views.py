"""Vistas del panel operativo.

El panel está pensado para el uso diario de los clientes: crear certificados,
descargarlos en PDF/HTML y administrar usuarios. La configuración avanzada
(plantillas, tipos de certificado, contenido del sitio) sigue disponible en el
administrador de Django.
"""

from __future__ import annotations

import re
from datetime import timedelta
from functools import wraps

from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils import translation
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from apps.accounts.models import User
from apps.certificates.models import (
    Certificate,
    CertificateEvent,
    ValidationLog,
    generate_token,
)
from apps.certificates.pdf import PDFRenderError, render_certificate_pdf
from apps.certificates.qr import make_qr_png
from apps.certificates.rendering import TemplateRenderError, render_certificate_html
from apps.core.i18n import normalize_document_lang, normalize_lang, tr_admin
from apps.core.utils import get_client_ip

from .forms import (
    PanelCertificateForm,
    PanelPasswordForm,
    PanelUserCreateForm,
    PanelUserEditForm,
)

PREVIEW_CSP = (
    "default-src 'none'; img-src data:; style-src 'unsafe-inline'; "
    "font-src data:; base-uri 'none'; form-action 'none'; frame-ancestors 'none'"
)

DOCUMENT_LANGUAGES = (
    {"code": "en", "name": "English"},
    {"code": "zh-hans", "name": "中文"},
    {"code": "es", "name": "Español"},
)

EVENT_LABEL_KEYS = {
    "created": "panel_event_created",
    "updated": "panel_event_updated",
    "status_changed": "panel_event_status_changed",
    "token_regenerated": "panel_event_token_regenerated",
    "rendered": "panel_event_rendered",
    "downloaded": "panel_event_downloaded",
    "pdf_downloaded": "panel_event_pdf_downloaded",
}


# ---------------------------------------------------------------------------
# Acceso y utilidades
# ---------------------------------------------------------------------------
def _lang() -> str:
    return normalize_lang(translation.get_language(), admin=True)


def _safe_filename(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", value or "certificate")
    return cleaned.strip("._") or "certificate"


def panel_required(view):
    """Permite el acceso solo a usuarios activos con acceso al panel."""

    @wraps(view)
    def wrapper(request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return redirect_to_login(request.get_full_path(), reverse("panel:login"))
        if not (user.is_active and user.is_staff):
            raise PermissionDenied
        return view(request, *args, **kwargs)

    return wrapper


def superadmin_required(view):
    """Reserva la gestión de usuarios al superadministrador."""

    @wraps(view)
    def wrapper(request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return redirect_to_login(request.get_full_path(), reverse("panel:login"))
        if not (user.is_active and user.is_superadmin):
            raise PermissionDenied
        return view(request, *args, **kwargs)

    return wrapper


def _log_event(request, certificate, event, message=""):
    CertificateEvent.objects.create(
        certificate=certificate,
        user=request.user if request.user.is_authenticated else None,
        event=event,
        message=(message or "")[:300],
        ip_address=get_client_ip(request),
    )


def _paginate(request, queryset, per_page=20):
    page = Paginator(queryset, per_page).get_page(request.GET.get("page"))
    params = request.GET.copy()
    params.pop("page", None)
    return page, params.urlencode()


def _label_events(events, lang: str) -> list:
    """Añade a cada evento su etiqueta traducida para la plantilla."""

    labeled = list(events)
    for event in labeled:
        key = EVENT_LABEL_KEYS.get(event.event)
        event.display_label = tr_admin(key, lang) if key else event.get_event_display()
    return labeled


def _status_choices() -> list[dict[str, str]]:
    lang = _lang()
    return [
        {"value": "", "label": tr_admin("panel_filter_all", lang)},
        {"value": "valid", "label": tr_admin("status_valid", lang)},
        {"value": "expired", "label": tr_admin("status_expired", lang)},
        {"value": "blocked", "label": tr_admin("status_blocked", lang)},
    ]


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
@panel_required
@require_GET
def dashboard(request):
    lang = _lang()
    today = timezone.localdate()
    week_ago = timezone.now() - timedelta(days=7)

    certificates = Certificate.objects.all()
    stats = {
        "total": certificates.count(),
        "valid": certificates.filter(
            status=Certificate.Status.ACTIVE, expiry_date__gte=today
        ).count(),
        "expired": certificates.filter(expiry_date__lt=today).count(),
        "blocked": certificates.filter(status=Certificate.Status.BLOCKED).count(),
        "expiring": certificates.filter(
            status=Certificate.Status.ACTIVE,
            expiry_date__gte=today,
            expiry_date__lte=today + timedelta(days=30),
        ).count(),
        "validations": ValidationLog.objects.filter(created_at__gte=week_ago).count(),
    }

    recent_certificates = Certificate.objects.select_related(
        "certificate_type", "template"
    )[:8]
    recent_events = _label_events(
        CertificateEvent.objects.select_related("certificate", "user")[:8], lang
    )

    return render(
        request,
        "panel/dashboard.html",
        {
            "nav": "dashboard",
            "stats": stats,
            "recent_certificates": recent_certificates,
            "recent_events": recent_events,
            "event_labels": EVENT_LABEL_KEYS,
            "lang": lang,
        },
    )


# ---------------------------------------------------------------------------
# Certificados
# ---------------------------------------------------------------------------
@panel_required
@require_GET
def certificate_list(request):
    lang = _lang()
    query = (request.GET.get("q") or "").strip()
    status_filter = (request.GET.get("status") or "").strip()
    today = timezone.localdate()

    certificates = Certificate.objects.select_related(
        "certificate_type", "template", "analyst"
    )
    if query:
        certificates = certificates.filter(
            Q(code__icontains=query)
            | Q(applicant__icontains=query)
            | Q(manufacturer__icontains=query)
            | Q(product__icontains=query)
            | Q(brand__icontains=query)
            | Q(models_text__icontains=query)
        )
    if status_filter == "valid":
        certificates = certificates.filter(
            status=Certificate.Status.ACTIVE, expiry_date__gte=today
        )
    elif status_filter == "expired":
        certificates = certificates.filter(expiry_date__lt=today)
    elif status_filter == "blocked":
        certificates = certificates.filter(status=Certificate.Status.BLOCKED)

    page, querystring = _paginate(request, certificates)

    return render(
        request,
        "panel/certificates/list.html",
        {
            "nav": "certificates",
            "page": page,
            "querystring": querystring,
            "query": query,
            "status_filter": status_filter,
            "status_choices": _status_choices(),
            "total_results": page.paginator.count,
            "lang": lang,
        },
    )


@panel_required
@require_GET
def certificate_detail(request, pk):
    lang = _lang()
    certificate = get_object_or_404(
        Certificate.objects.select_related(
            "certificate_type", "template", "analyst"
        ),
        pk=pk,
    )
    events = _label_events(
        certificate.events.select_related("user")[:12], lang
    )
    return render(
        request,
        "panel/certificates/detail.html",
        {
            "nav": "certificates",
            "certificate": certificate,
            "events": events,
            "event_labels": EVENT_LABEL_KEYS,
            "document_languages": DOCUMENT_LANGUAGES,
            "lang": lang,
        },
    )


@panel_required
@require_http_methods(["GET", "POST"])
def certificate_create(request):
    lang = _lang()
    form = PanelCertificateForm(
        request.POST or None, request.FILES or None
    )
    if request.method == "POST" and form.is_valid():
        certificate = form.save(commit=False)
        if not certificate.analyst_id:
            certificate.analyst = request.user
        certificate.save()
        _log_event(request, certificate, CertificateEvent.Event.CREATED)
        messages.success(request, tr_admin("panel_certificate_created", lang))
        return redirect("panel:certificate_detail", pk=certificate.pk)

    return render(
        request,
        "panel/certificates/form.html",
        {
            "nav": "certificates",
            "form": form,
            "groups": _certificate_groups(form, lang),
            "is_edit": False,
            "lang": lang,
        },
    )


@panel_required
@require_http_methods(["GET", "POST"])
def certificate_edit(request, pk):
    lang = _lang()
    certificate = get_object_or_404(Certificate, pk=pk)
    form = PanelCertificateForm(
        request.POST or None, request.FILES or None, instance=certificate
    )
    if request.method == "POST" and form.is_valid():
        certificate = form.save(commit=False)
        if not certificate.analyst_id:
            certificate.analyst = request.user
        certificate.save()
        event = CertificateEvent.Event.UPDATED
        if "status" in form.changed_data:
            event = CertificateEvent.Event.STATUS_CHANGED
        _log_event(request, certificate, event)
        messages.success(request, tr_admin("panel_certificate_updated", lang))
        return redirect("panel:certificate_detail", pk=certificate.pk)

    return render(
        request,
        "panel/certificates/form.html",
        {
            "nav": "certificates",
            "form": form,
            "groups": _certificate_groups(form, lang),
            "certificate": certificate,
            "is_edit": True,
            "lang": lang,
        },
    )


def _certificate_groups(form, lang):
    """Agrupa los campos del formulario para la plantilla."""

    return [
        {
            "title": tr_admin("panel_group_data", lang),
            "fields": [
                form[name]
                for name in (
                    "code",
                    "certificate_type",
                    "applicant",
                    "manufacturer",
                    "manufacturer_address",
                    "product",
                    "brand",
                    "product_description",
                )
            ],
        },
        {
            "title": tr_admin("panel_group_models", lang),
            "fields": [form["models_text"], form["models_csv"]],
        },
        {
            "title": tr_admin("panel_group_testing", lang),
            "fields": [
                form["test_parameters"],
                form["show_parameters"],
                form["test_standards"],
                form["test_report"],
            ],
        },
        {
            "title": tr_admin("panel_group_dates", lang),
            "fields": [form["issue_date"], form["expiry_date"], form["status"]],
        },
        {
            "title": tr_admin("panel_group_publication", lang),
            "fields": [form["template"]],
        },
    ]


@panel_required
@require_POST
def certificate_status(request, pk):
    lang = _lang()
    certificate = get_object_or_404(Certificate, pk=pk)
    if certificate.status == Certificate.Status.ACTIVE:
        certificate.status = Certificate.Status.BLOCKED
        key = "panel_certificate_suspended"
    else:
        certificate.status = Certificate.Status.ACTIVE
        key = "panel_certificate_activated"
    certificate.save(update_fields=["status", "updated_at"])
    _log_event(request, certificate, CertificateEvent.Event.STATUS_CHANGED)
    messages.success(request, tr_admin(key, lang))
    return redirect("panel:certificate_detail", pk=certificate.pk)


@panel_required
@require_POST
def certificate_regenerate_token(request, pk):
    lang = _lang()
    certificate = get_object_or_404(Certificate, pk=pk)
    certificate.token = generate_token()
    certificate.save(update_fields=["token", "updated_at"])
    _log_event(request, certificate, CertificateEvent.Event.TOKEN_REGENERATED)
    messages.success(request, tr_admin("panel_token_regenerated", lang))
    return redirect("panel:certificate_detail", pk=certificate.pk)


@panel_required
@require_GET
def certificate_pdf(request, pk, lang):
    certificate = get_object_or_404(Certificate, pk=pk)
    lang = normalize_document_lang(lang)
    download = request.GET.get("download") == "1"
    try:
        pdf = render_certificate_pdf(certificate, lang=lang)
    except (TemplateRenderError, PDFRenderError) as exc:
        messages.error(request, str(exc))
        return redirect("panel:certificate_detail", pk=certificate.pk)

    _log_event(
        request, certificate, CertificateEvent.Event.PDF_DOWNLOADED, message=lang
    )
    filename = f"certificate-{_safe_filename(certificate.code)}-{lang}.pdf"
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = (
        f'{"attachment" if download else "inline"}; filename="{filename}"'
    )
    response["Cache-Control"] = "private, no-store"
    return response


@panel_required
@require_GET
def certificate_html(request, pk, lang):
    certificate = get_object_or_404(Certificate, pk=pk)
    lang = normalize_document_lang(lang)
    download = request.GET.get("download") == "1"
    try:
        html = render_certificate_html(certificate, lang=lang)
    except TemplateRenderError as exc:
        messages.error(request, str(exc))
        return redirect("panel:certificate_detail", pk=certificate.pk)

    _log_event(
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


@panel_required
@require_GET
def certificate_qr(request, pk):
    certificate = get_object_or_404(Certificate, pk=pk)
    png = make_qr_png(certificate.validation_url)
    response = HttpResponse(png, content_type="image/png")
    if request.GET.get("download") == "1":
        filename = f"qr-{_safe_filename(certificate.code)}.png"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
    response["Cache-Control"] = "private, max-age=300"
    return response


# ---------------------------------------------------------------------------
# Actividad
# ---------------------------------------------------------------------------
@panel_required
@require_GET
def activity(request):
    lang = _lang()
    event_filter = (request.GET.get("event") or "").strip()
    events = CertificateEvent.objects.select_related("certificate", "user")
    if event_filter in EVENT_LABEL_KEYS:
        events = events.filter(event=event_filter)
    page, querystring = _paginate(request, events, per_page=30)
    page.object_list = _label_events(page.object_list, lang)
    event_choices = [
        {"value": value, "label": tr_admin(key, lang)}
        for value, key in EVENT_LABEL_KEYS.items()
    ]
    return render(
        request,
        "panel/activity.html",
        {
            "nav": "activity",
            "page": page,
            "querystring": querystring,
            "event_filter": event_filter,
            "event_choices": event_choices,
            "event_labels": EVENT_LABEL_KEYS,
            "lang": lang,
        },
    )


# ---------------------------------------------------------------------------
# Usuarios (solo superadministrador)
# ---------------------------------------------------------------------------
@superadmin_required
@require_GET
def user_list(request):
    lang = _lang()
    query = (request.GET.get("q") or "").strip()
    users = User.objects.all()
    if query:
        users = users.filter(
            Q(email__icontains=query) | Q(full_name__icontains=query)
        )
    page, querystring = _paginate(request, users)
    return render(
        request,
        "panel/users/list.html",
        {
            "nav": "users",
            "page": page,
            "querystring": querystring,
            "query": query,
            "total_results": page.paginator.count,
            "lang": lang,
        },
    )


@superadmin_required
@require_http_methods(["GET", "POST"])
def user_create(request):
    lang = _lang()
    form = PanelUserCreateForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        messages.success(
            request,
            tr_admin("panel_user_created", lang, email=user.email),
        )
        return redirect("panel:user_list")
    return render(
        request,
        "panel/users/form.html",
        {"nav": "users", "form": form, "is_edit": False, "lang": lang},
    )


@superadmin_required
@require_http_methods(["GET", "POST"])
def user_edit(request, pk):
    lang = _lang()
    user = get_object_or_404(User, pk=pk)
    form = PanelUserEditForm(request.POST or None, instance=user)
    if request.method == "POST" and form.is_valid():
        if user == request.user:
            if not form.cleaned_data.get("is_active"):
                form.add_error("is_active", tr_admin("panel_cannot_deactivate_self", lang))
            if form.cleaned_data.get("role") != User.Role.SUPERADMIN:
                form.add_error("role", tr_admin("panel_cannot_demote_self", lang))
        if not form.errors:
            form.save()
            messages.success(
                request,
                tr_admin("panel_user_updated", lang, email=user.email),
            )
            return redirect("panel:user_list")
    return render(
        request,
        "panel/users/form.html",
        {
            "nav": "users",
            "form": form,
            "is_edit": True,
            "target_user": user,
            "lang": lang,
        },
    )


@superadmin_required
@require_http_methods(["GET", "POST"])
def user_password(request, pk):
    lang = _lang()
    user = get_object_or_404(User, pk=pk)
    form = PanelPasswordForm(user, request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        if user == request.user:
            update_session_auth_hash(request, user)
        messages.success(
            request,
            tr_admin("panel_password_changed", lang, email=user.email),
        )
        return redirect("panel:user_list")
    return render(
        request,
        "panel/users/password.html",
        {"nav": "users", "form": form, "target_user": user, "lang": lang},
    )
