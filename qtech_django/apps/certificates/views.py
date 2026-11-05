"""Validación pública de certificados.

Esta vista es la única parte del sistema de certificados expuesta en la web
pública. No muestra el panel administrativo ni permite modificar datos: solo
confirma si un certificado existe y si está vigente.
"""

from __future__ import annotations

import logging

from django.db.models import Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils import translation
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods

from apps.core.i18n import normalize_lang, tr
from apps.core.utils import get_client_ip, rate_limit

from .models import Certificate, ValidationLog

logger = logging.getLogger("qtech")

MAX_QUERY_LENGTH = 200
RATE_LIMIT_ATTEMPTS = 40
RATE_LIMIT_WINDOW = 10 * 60  # 10 minutos


def _clean_query(value: str | None) -> str:
    return (value or "").strip()[:MAX_QUERY_LENGTH]


def _find_certificate(query: str) -> Certificate | None:
    """Busca por token exacto o por número de certificado sin distinguir mayúsculas."""

    if not query:
        return None
    return (
        Certificate.objects.select_related("certificate_type", "template")
        .filter(Q(token=query) | Q(code__iexact=query))
        .first()
    )


def _log_validation(
    request: HttpRequest,
    query: str,
    result: str,
    certificate: Certificate | None = None,
) -> None:
    try:
        ValidationLog.objects.create(
            certificate=certificate,
            query=query[:MAX_QUERY_LENGTH],
            result=result,
            success=certificate is not None,
            ip_address=get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", "")[:300],
        )
    except Exception:  # pragma: no cover - el registro nunca debe romper la consulta
        logger.exception("No se pudo registrar el intento de validación")


@never_cache
@require_http_methods(["GET"])
def verify(request: HttpRequest) -> HttpResponse:
    lang = normalize_lang(request.GET.get("lang") or translation.get_language())
    translation.activate(lang)

    query = _clean_query(
        request.GET.get("token")
        or request.GET.get("q")
        or request.GET.get("code")
        or ""
    )

    certificate: Certificate | None = None
    result = ""
    rate_limited = False

    if query:
        allowed, _remaining = rate_limit(
            f"verify-ip:{get_client_ip(request)}",
            limit=RATE_LIMIT_ATTEMPTS,
            window=RATE_LIMIT_WINDOW,
        )
        if not allowed:
            result = "rate_limited"
            rate_limited = True
            _log_validation(request, query, ValidationLog.Result.RATE_LIMITED)
        else:
            certificate = _find_certificate(query)
            if certificate is None:
                result = "not_found"
                _log_validation(request, query, ValidationLog.Result.NOT_FOUND)
            elif certificate.computed_status == "blocked":
                result = "blocked"
                _log_validation(
                    request, query, ValidationLog.Result.BLOCKED, certificate
                )
            elif certificate.computed_status == "expired":
                result = "expired"
                _log_validation(
                    request, query, ValidationLog.Result.EXPIRED, certificate
                )
            else:
                result = "valid"
                _log_validation(
                    request, query, ValidationLog.Result.VALID, certificate
                )

    data: dict = {}
    models: list[str] = []
    type_label = ""
    status_label = ""
    if certificate is not None:
        data = certificate.data_for_language(lang)
        models = certificate.models_list
        type_label = certificate.type_label(lang)
        status_label = certificate.status_label(lang)

    title_keys = {
        "valid": "verify_valid",
        "expired": "verify_expired",
        "blocked": "verify_blocked",
        "not_found": "verify_not_found_title",
        "rate_limited": "verify_rate_title",
    }
    description_keys = {
        "valid": "verify_valid_desc",
        "expired": "verify_expired_desc",
        "blocked": "verify_blocked_desc",
        "not_found": "verify_not_found_desc",
        "rate_limited": "verify_rate_desc",
    }
    context = {
        "query": query,
        "certificate": certificate,
        "result": result,
        "rate_limited": rate_limited,
        "data": data,
        "models": models,
        "models_count": len(models),
        "type_label": type_label,
        "status_label": status_label,
        "meta_title": tr("verify_meta_title", lang=lang),
        "meta_description": tr("verify_subtitle", lang=lang),
        "result_title": tr(title_keys[result], lang=lang) if result else "",
        "result_description": tr(description_keys[result], lang=lang)
        if result
        else "",
        "result_tone": {
            "valid": "valid",
            "expired": "expired",
            "blocked": "blocked",
            "not_found": "invalid",
            "rate_limited": "invalid",
        }.get(result, "neutral"),
    }
    return render(request, "certificates/verify.html", context)
