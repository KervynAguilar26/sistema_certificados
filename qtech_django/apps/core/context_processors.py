"""Context processors compartidos por las plantillas."""

from __future__ import annotations

from django.conf import settings
from django.utils import timezone

from .i18n import (
    LANGUAGE_NAMES,
    LazyTr,
    admin_language_choices,
    current_lang,
    language_choices,
)
from .models import SiteSettings


def site_context(request):
    try:
        site = SiteSettings.load()
    except Exception:
        # Durante las migraciones o si la base de datos aún no está lista.
        site = SiteSettings()
    return {
        "site": site,
        "current_year": timezone.localdate().year,
    }


def i18n_context(request):
    lang = current_lang()
    return {
        "t": LazyTr(lang),
        "current_language": lang,
        "public_languages": language_choices(),
        "admin_languages": admin_language_choices(),
        "language_names": LANGUAGE_NAMES,
        "admin_url_path": settings.ADMIN_URL_PATH,
    }
