"""Sitio administrativo personalizado de QTech."""

from __future__ import annotations

from datetime import timedelta

from django.conf import settings
from django.contrib.admin import AdminSite
from django.utils import timezone, translation
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache

from .i18n import (
    LazyTr,
    admin_language_choices,
    get_translations,
    language_choices,
    normalize_lang,
    tr_admin,
)


@method_decorator(never_cache, name="index")
class QTechAdminSite(AdminSite):
    """Panel privado con textos traducidos y tablero de control."""

    site_header = "QTech Certification System"
    site_title = "QTech Certification"
    index_title = "Control panel"
    login_template = "admin/login.html"
    logout_template = "admin/logout.html"
    index_template = "admin/index.html"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Importación diferida para evitar ciclos durante la carga de apps.
        from apps.accounts.forms import QTechAdminAuthenticationForm

        self.login_form = QTechAdminAuthenticationForm

    # ------------------------------------------------------------------
    # Traducciones del panel
    # ------------------------------------------------------------------
    @staticmethod
    def _translated(key: str, lang: str, default: str) -> str:
        return get_translations(lang).get(key, default)

    def get_app_list(self, request, app_label=None):
        app_list = super().get_app_list(request, app_label)
        lang = normalize_lang(translation.get_language(), admin=True)
        for app in app_list:
            app_key = f"admin_app_{app['app_label']}"
            app["name"] = self._translated(app_key, lang, app["name"])
            for model in app["models"]:
                model_key = (
                    f"admin_model_{app['app_label']}_{model['object_name'].lower()}"
                )
                model["name"] = self._translated(model_key, lang, model["name"])
        app_list.sort(key=lambda item: item["name"].lower())
        return app_list

    def each_context(self, request):
        context = super().each_context(request)
        lang = normalize_lang(translation.get_language(), admin=True)
        context.update(
            {
                "site_header": tr_admin("admin_site_header", lang),
                "site_title": tr_admin("admin_site_title", lang),
                "index_title": tr_admin("admin_index_title", lang),
                "qtech_lang": lang,
                "qtech_t": LazyTr(lang),
                "qtech_admin_languages": admin_language_choices(),
                "qtech_public_languages": language_choices(),
                "qtech_public_url": settings.SITE_BASE_URL,
                "qtech_admin_url": "/" + settings.ADMIN_URL_PATH,
                "qtech_session_minutes": settings.SESSION_COOKIE_AGE // 60,
            }
        )
        return context

    # ------------------------------------------------------------------
    # Tablero
    # ------------------------------------------------------------------
    def _dashboard_context(self) -> dict:
        from apps.certificates.models import (
            Certificate,
            CertificateEvent,
            ValidationLog,
        )
        from apps.core.models import ContactMessage

        today = timezone.localdate()
        now = timezone.now()
        active_qs = Certificate.objects.filter(status=Certificate.Status.ACTIVE)
        recent_certificates = (
            Certificate.objects.select_related("certificate_type", "analyst")
            .order_by("-created_at")[:8]
        )
        recent_events = (
            CertificateEvent.objects.select_related("certificate", "user")
            .order_by("-created_at")[:8]
        )
        recent_messages = ContactMessage.objects.order_by("-created_at")[:5]
        return {
            "qtech_stats": {
                "total": Certificate.objects.count(),
                "active": active_qs.filter(expiry_date__gte=today).count(),
                "blocked": Certificate.objects.filter(
                    status=Certificate.Status.BLOCKED
                ).count(),
                "expired": active_qs.filter(expiry_date__lt=today).count(),
                "expiring_soon": active_qs.filter(
                    expiry_date__gte=today,
                    expiry_date__lte=today + timedelta(days=30),
                ).count(),
                "validations_7d": ValidationLog.objects.filter(
                    created_at__gte=now - timedelta(days=7)
                ).count(),
                "unread_messages": ContactMessage.objects.filter(
                    is_read=False
                ).count(),
            },
            "qtech_recent_certificates": recent_certificates,
            "qtech_recent_events": recent_events,
            "qtech_recent_messages": recent_messages,
        }

    def index(self, request, extra_context=None):
        context = self._dashboard_context()
        if extra_context:
            context.update(extra_context)
        return super().index(request, extra_context=context)
