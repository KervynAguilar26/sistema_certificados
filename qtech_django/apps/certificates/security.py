"""Validación de plantillas HTML de certificados.

Las plantillas se cargan desde el panel privado y se renderizan con el motor de
Django. Para evitar ejecución de código o fugas de información se aplican estas
reglas antes de guardar y antes de renderizar:

* límite de tamaño;
* etiquetas HTML peligrosas prohibidas;
* controladores de eventos y esquemas ``javascript:`` prohibidos;
* solo se permiten las etiquetas ``{% if %}``, ``{% for %}``, ``{% with %}`` y
  ``{% comment %}``;
* solo se permiten filtros de presentación seguros.
"""

from __future__ import annotations

import re

from django.core.exceptions import ValidationError

MAX_TEMPLATE_BYTES = 1_000_000

_ALLOWED_TAGS = {
    "if",
    "else",
    "endif",
    "for",
    "empty",
    "endfor",
    "with",
    "endwith",
    "comment",
    "endcomment",
}

_ALLOWED_FILTERS = {
    "default",
    "default_if_none",
    "escape",
    "date",
    "time",
    "lower",
    "upper",
    "title",
    "capfirst",
    "length",
    "join",
    "linebreaks",
    "linebreaksbr",
    "truncatechars",
    "truncatewords",
    "floatformat",
    "yesno",
    "striptags",
    "cut",
    "stringformat",
    "add",
    "first",
    "last",
}

_FORBIDDEN_HTML = re.compile(
    r"<\s*(script|iframe|object|embed|form|input|button|textarea|select|option|base|link)\b",
    re.IGNORECASE,
)
_FORBIDDEN_META = re.compile(r"<\s*meta\b[^>]*http-equiv", re.IGNORECASE)
_EVENT_HANDLER = re.compile(r"\son[a-z]{3,}\s*=", re.IGNORECASE)
_DANGEROUS_URL = re.compile(
    r"(?:javascript|vbscript)\s*:|data\s*:\s*text/html|srcdoc\s*=", re.IGNORECASE
)
_DANGEROUS_CSS = re.compile(
    r"@import|expression\s*\(|behavior\s*:|-moz-binding|"
    r"url\s*\(\s*['\"]?\s*(?:https?:|//|javascript:)",
    re.IGNORECASE,
)
_TAG_RE = re.compile(r"{%\s*(.*?)\s*%}", re.DOTALL)
_VAR_RE = re.compile(r"{{\s*(.*?)\s*}}", re.DOTALL)
_FILTER_RE = re.compile(r"\|\s*([a-zA-Z_][a-zA-Z0-9_]*)")

FORBIDDEN_TAGS = ("script", "iframe", "object", "embed", "form", "input", "base", "link")


def _check_variables(source: str) -> None:
    for match in _VAR_RE.finditer(source):
        expression = match.group(1).strip()
        if not expression:
            continue
        if "__" in expression or re.search(r"(^|[.\s(])_", expression):
            raise ValidationError("La plantilla contiene una variable no permitida.")
        if re.search(r"\b(settings|request|user|perms|csrf_token|password|secret)\b", expression):
            raise ValidationError("La plantilla intenta acceder a una variable reservada.")
        for filter_name in _FILTER_RE.findall(expression):
            if filter_name not in _ALLOWED_FILTERS:
                raise ValidationError(
                    f"El filtro «{filter_name}» no está permitido en las plantillas."
                )


def _check_tags(source: str) -> None:
    for match in _TAG_RE.finditer(source):
        content = match.group(1).strip()
        if not content:
            continue
        tag = content.split(None, 1)[0].lower()
        if tag not in _ALLOWED_TAGS:
            raise ValidationError(
                f"La etiqueta «{{% {tag} %}}» no está permitida. "
                "Use únicamente if, for, with y comment."
            )


def validate_certificate_template(source: str) -> None:
    """Lanza ``ValidationError`` si la plantilla no es segura."""

    if not source or not source.strip():
        raise ValidationError("La plantilla está vacía.")
    if len(source.encode("utf-8")) > MAX_TEMPLATE_BYTES:
        raise ValidationError("La plantilla supera el tamaño máximo de 1 MB.")
    if _FORBIDDEN_HTML.search(source):
        raise ValidationError(
            "La plantilla contiene etiquetas HTML no permitidas "
            "(script, iframe, form, input, etc.)."
        )
    if _FORBIDDEN_META.search(source):
        raise ValidationError("La plantilla no puede incluir redirecciones meta.")
    if _EVENT_HANDLER.search(source):
        raise ValidationError("La plantilla no puede incluir controladores de eventos (onclick, onload, etc.).")
    if _DANGEROUS_URL.search(source):
        raise ValidationError("La plantilla contiene una URL o un esquema peligroso.")
    if _DANGEROUS_CSS.search(source):
        raise ValidationError(
            "La plantilla no puede cargar recursos externos desde CSS ni usar expresiones."
        )
    _check_tags(source)
    _check_variables(source)


def validate_template_file(uploaded_file) -> str:
    """Lee un archivo subido y devuelve su contenido validado."""

    if uploaded_file is None:
        raise ValidationError("Seleccione un archivo HTML.")
    if uploaded_file.size > MAX_TEMPLATE_BYTES:
        raise ValidationError("El archivo supera el tamaño máximo de 1 MB.")
    name = (getattr(uploaded_file, "name", "") or "").lower()
    if not (name.endswith(".html") or name.endswith(".htm")):
        raise ValidationError("El archivo debe tener extensión .html o .htm.")
    raw = uploaded_file.read()
    uploaded_file.seek(0)
    try:
        source = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        try:
            source = raw.decode("latin-1")
        except UnicodeDecodeError as exc:
            raise ValidationError("El archivo debe estar codificado en UTF-8.") from exc
    validate_certificate_template(source)
    return source
