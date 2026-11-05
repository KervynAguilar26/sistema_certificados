"""Capa de traducción ligera basada en diccionarios.

El proyecto no depende de archivos gettext compilados: los textos viven en
``apps/core/translations`` y se resuelven en tiempo de ejecución. La web pública
y el panel administrativo están disponibles solo en chino e inglés.

El diccionario español se conserva únicamente para los certificados (PDF/HTML),
que se pueden emitir en español, inglés o chino.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from django.utils import translation

from .translations import EN, ES, ZH

PUBLIC_LANGUAGES = ("zh-hans", "en")
ADMIN_LANGUAGES = ("zh-hans", "en")
DOCUMENT_LANGUAGES = ("zh-hans", "en", "es")

LANGUAGE_NAMES = {
    "zh-hans": "中文",
    "en": "English",
    "es": "Español",
}

_ALIASES = {
    "zh": "zh-hans",
    "zh-cn": "zh-hans",
    "zh-hans": "zh-hans",
    "zh-hant": "zh-hans",
    "cn": "zh-hans",
    "en": "en",
    "en-us": "en",
    "en-gb": "en",
    "es": "es",
    "es-es": "es",
    "es-ve": "es",
    "es-mx": "es",
}

_DICTIONARIES = {
    "en": EN,
    "es": ES,
    "zh-hans": ZH,
}


def _resolve_lang(code: str | None) -> str:
    """Convierte cualquier código en uno de los idiomas con diccionario."""

    if not code:
        code = translation.get_language() or "zh-hans"
    code = str(code).strip().lower().replace("_", "-")
    lang = _ALIASES.get(code)
    if lang is None:
        base = code.split("-", 1)[0]
        lang = _ALIASES.get(base, "zh-hans")
    return lang


def normalize_lang(code: str | None, *, admin: bool = False) -> str:
    """Devuelve un idioma permitido en la interfaz.

    La web pública y el panel solo admiten chino e inglés. ``admin`` se mantiene
    como parámetro explícito por claridad, aunque ambas listas coinciden hoy.
    """

    lang = _resolve_lang(code)
    allowed = ADMIN_LANGUAGES if admin else PUBLIC_LANGUAGES
    return lang if lang in allowed else "zh-hans"


def normalize_document_lang(code: str | None) -> str:
    """Idioma permitido en los certificados (PDF/HTML).

    Los documentos sí pueden emitirse en español, aunque la web y el panel no.
    """

    lang = _resolve_lang(code)
    return lang if lang in DOCUMENT_LANGUAGES else "zh-hans"


def current_lang(*, admin: bool = False) -> str:
    return normalize_lang(translation.get_language(), admin=admin)


@lru_cache(maxsize=None)
def get_translations(lang: str) -> dict[str, str]:
    lang = _resolve_lang(lang)
    # Combinamos inglés como respaldo para que una clave nueva nunca rompa una
    # página. El diccionario específico tiene prioridad.
    merged = dict(EN)
    merged.update(_DICTIONARIES.get(lang, {}))
    return merged


def tr(key: str, lang: str | None = None, **kwargs: Any) -> str:
    """Traduce una clave y aplica formato opcional."""

    lang = _resolve_lang(lang) if lang else current_lang()
    value = get_translations(lang).get(key)
    if value is None:
        value = EN.get(key, key)
    if kwargs:
        try:
            return str(value).format(**kwargs)
        except (KeyError, IndexError, ValueError):
            return str(value)
    return str(value)


def tr_admin(key: str, lang: str | None = None, **kwargs: Any) -> str:
    lang = normalize_lang(lang, admin=True) if lang else current_lang(admin=True)
    return tr(key, lang=lang, **kwargs)


class LazyTr:
    """Objeto compatible con plantillas: ``{{ t.nav_home }}``."""

    def __init__(self, lang: str | None = None):
        self.lang = _resolve_lang(lang) if lang else current_lang()

    def __getattr__(self, key: str) -> str:
        if key.startswith("_"):
            raise AttributeError(key)
        return tr(key, self.lang)

    def __getitem__(self, key: str) -> str:
        return tr(key, self.lang)

    def get(self, key: str, default: str | None = None) -> str:
        return tr(key, self.lang) if key in get_translations(self.lang) else (default or key)


def language_choices() -> list[dict[str, str]]:
    return [
        {"code": code, "name": LANGUAGE_NAMES[code]}
        for code in PUBLIC_LANGUAGES
    ]


def admin_language_choices() -> list[dict[str, str]]:
    return [
        {"code": code, "name": LANGUAGE_NAMES[code]}
        for code in ADMIN_LANGUAGES
    ]
