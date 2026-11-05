"""Vistas de la web pública."""

from __future__ import annotations

import json
import logging

from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.db import connection
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import translation
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .forms import ContactForm
from .i18n import ADMIN_LANGUAGES, PUBLIC_LANGUAGES, normalize_lang, tr
from .models import ContactMessage, GalleryImage, HeroSlide, Service, SiteSettings, TeamMember
from .utils import get_client_ip, rate_limit

logger = logging.getLogger("qtech")


def _public_context(request) -> dict:
    site = SiteSettings.load()
    return {
        "site": site,
        "hero_slides": HeroSlide.objects.filter(is_active=True),
        "services": Service.objects.filter(is_active=True),
        "team_members": TeamMember.objects.filter(is_active=True),
        "gallery_images": GalleryImage.objects.filter(is_active=True),
        "contact_form": ContactForm(),
    }


@csrf_protect
@require_http_methods(["GET", "POST"])
def home(request):
    site = SiteSettings.load()
    context = _public_context(request)
    context["meta_title"] = site.meta_title or site.site_name
    context["meta_description"] = site.meta_description or tr("home_meta_description")

    if request.method == "POST":
        form = ContactForm(request.POST)
        context["contact_form"] = form
        if form.is_valid():
            # Honeypot: respondemos como si todo hubiera ido bien.
            if form.cleaned_data.get("website"):
                messages.success(request, tr("form_success"))
                return redirect(f"{reverse('core:home')}#contacto")

            allowed, _ = rate_limit(
                f"contact:{get_client_ip(request)}", limit=5, window=60 * 60
            )
            if not allowed:
                messages.error(request, tr("verify_rate_desc"))
                return redirect(f"{reverse('core:home')}#contacto")

            data = form.cleaned_data
            contact = ContactMessage.objects.create(
                name=data["name"],
                email=data["email"],
                phone=data.get("phone", ""),
                company=data.get("company", ""),
                message=data["message"],
                ip_address=get_client_ip(request),
                user_agent=request.META.get("HTTP_USER_AGENT", "")[:300],
            )
            try:
                send_mail(
                    subject=f"[{site.site_name}] {tr('contact_title')}",
                    message=(
                        f"{tr('form_name')}: {contact.name}\n"
                        f"{tr('form_email')}: {contact.email}\n"
                        f"{tr('form_phone')}: {contact.phone}\n"
                        f"{tr('form_company')}: {contact.company}\n\n"
                        f"{contact.message}"
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[settings.CONTACT_EMAIL],
                    fail_silently=True,
                )
            except Exception:  # pragma: no cover - el correo nunca debe romper el formulario
                logger.exception("No se pudo enviar el correo de contacto")
            messages.success(request, tr("form_success"))
            return redirect(f"{reverse('core:home')}#contacto")
        messages.error(request, tr("form_error"))
    return render(request, "core/home.html", context)


@csrf_protect
@require_POST
def contact(request):
    """Alias POST para formularios sin JavaScript que apunten a /contacto/."""

    return home(request)


@require_GET
def set_language(request):
    """Cambia el idioma de la web pública o del panel administrativo."""

    lang = request.GET.get("lang") or request.POST.get("lang") or ""
    next_url = request.GET.get("next") or request.POST.get("next") or "/"
    if not url_has_allowed_host_and_scheme(
        next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        next_url = "/"

    admin_prefix = "/" + settings.ADMIN_URL_PATH
    is_admin = next_url.startswith(admin_prefix)
    normalized = normalize_lang(lang, admin=is_admin)
    allowed = ADMIN_LANGUAGES if is_admin else PUBLIC_LANGUAGES
    if normalized not in allowed:
        normalized = "zh-hans"

    translation.activate(normalized)
    response = redirect(next_url)
    response.set_cookie(
        settings.LANGUAGE_COOKIE_NAME,
        normalized,
        max_age=settings.LANGUAGE_COOKIE_AGE,
        path=settings.LANGUAGE_COOKIE_PATH,
        domain=settings.LANGUAGE_COOKIE_DOMAIN,
        secure=settings.SESSION_COOKIE_SECURE,
        httponly=False,
        samesite="Lax",
    )
    return response


@require_GET
def robots_txt(request):
    lines = [
        "User-agent: *",
        "Disallow: /" + settings.ADMIN_URL_PATH,
        "Disallow: /panel/",
        "Disallow: /verify/",
        f"Sitemap: {settings.SITE_BASE_URL}/sitemap.xml",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain; charset=utf-8")


@never_cache
@require_GET
def health(request):
    status = {"status": "ok", "database": "ok"}
    code = 200
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception:
        logger.exception("Health check: base de datos no disponible")
        status = {"status": "error", "database": "error"}
        code = 503
    return JsonResponse(status, status=code)
