"""Etiquetas y filtros de plantilla de QTech."""

from __future__ import annotations

import base64
import mimetypes
from pathlib import Path

from django import template
from django.contrib.staticfiles import finders
from django.urls import reverse
from django.utils.http import urlencode

from apps.core.i18n import normalize_lang, tr

register = template.Library()


@register.filter
def data_uri(value) -> str:
    """Convierte un FieldFile en un data URI (para certificados y correos)."""

    if not value:
        return ""
    try:
        value.open("rb")
        raw = value.read()
        name = getattr(value, "name", "") or ""
    except Exception:
        return ""
    finally:
        try:
            value.close()
        except Exception:
            pass
    mime = mimetypes.guess_type(name)[0] or "application/octet-stream"
    return f"data:{mime};base64,{base64.b64encode(raw).decode('ascii')}"


@register.simple_tag
def static_data_uri(path: str) -> str:
    """Incrusta un archivo estático como data URI."""

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


@register.simple_tag
def tr_tag(key: str, lang: str | None = None, **kwargs) -> str:
    return tr(key, lang=lang, **kwargs)


@register.filter
def status_tone(value: str) -> str:
    return {
        "valid": "valid",
        "expired": "expired",
        "blocked": "blocked",
        "activo": "valid",
        "bloqueado": "blocked",
    }.get(str(value).lower(), "neutral")


@register.simple_tag
def language_url(request, lang: str) -> str:
    """URL para cambiar de idioma conservando la página actual."""

    next_url = request.get_full_path() if request else "/"
    return f"{reverse('set_language')}?{urlencode({'lang': lang, 'next': next_url})}"


@register.simple_tag
def admin_language_url(request, lang: str) -> str:
    next_url = request.get_full_path() if request else "/"
    return (
        f"{reverse('set_language')}?"
        f"{urlencode({'lang': normalize_lang(lang, admin=True), 'next': next_url})}"
    )
