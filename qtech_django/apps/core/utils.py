"""Utilidades compartidas: IP del cliente y limitación de intentos."""

from __future__ import annotations

from django.conf import settings
from django.core.cache import cache


def get_client_ip(request) -> str:
    """Obtiene la IP real solo si la aplicación está detrás de un proxy confiable."""

    if getattr(settings, "TRUST_PROXY_HEADERS", False):
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
        if forwarded:
            return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "0.0.0.0") or "0.0.0.0"


def rate_limit(key: str, limit: int, window: int) -> tuple[bool, int]:
    """Incrementa un contador y devuelve ``(permitido, restantes)``.

    Se usa el backend de caché configurado. En producción se recomienda Redis o
    Memcached para que el límite sea compartido entre procesos.
    """

    cache.add(key, 0, timeout=window)
    try:
        count = cache.incr(key)
    except ValueError:
        cache.set(key, 1, timeout=window)
        count = 1
    return count <= limit, max(0, limit - count)


def rate_limit_peek(key: str) -> int:
    return int(cache.get(key, 0) or 0)


def reset_rate_limit(key: str) -> None:
    cache.delete(key)
