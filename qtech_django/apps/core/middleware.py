"""Middleware de idioma del panel y cabeceras de seguridad."""

from __future__ import annotations

from django.conf import settings
from django.utils import translation

from .i18n import normalize_lang


class AdminLanguageMiddleware:
    """Restringe el panel privado a chino e inglés."""

    def __init__(self, get_response):
        self.get_response = get_response
        self.admin_prefix = "/" + settings.ADMIN_URL_PATH
        self.panel_prefix = "/panel/"

    def __call__(self, request):
        if request.path.startswith((self.admin_prefix, self.panel_prefix)):
            requested = request.GET.get("lang") or request.COOKIES.get(
                settings.LANGUAGE_COOKIE_NAME
            )
            lang = normalize_lang(requested, admin=True)
            translation.activate(lang)
            request.LANGUAGE_CODE = lang
        return self.get_response(request)


class SecurityHeadersMiddleware:
    """Añade cabeceras defensivas sin romper el admin de Django."""

    def __init__(self, get_response):
        self.get_response = get_response
        self.admin_prefix = "/" + settings.ADMIN_URL_PATH
        self.panel_prefix = "/panel/"

    def __call__(self, request):
        response = self.get_response(request)
        is_admin = request.path.startswith((self.admin_prefix, self.panel_prefix))

        response.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        response.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.setdefault("Cross-Origin-Opener-Policy", "same-origin")

        if is_admin:
            response.setdefault("Cache-Control", "no-store, private")
        elif request.path.startswith("/verify/"):
            response.setdefault("Cache-Control", "no-store")
            response.setdefault(
                "Content-Security-Policy",
                "default-src 'self'; img-src 'self' data:; "
                "style-src 'self' 'unsafe-inline'; script-src 'self'; "
                "font-src 'self'; object-src 'none'; base-uri 'self'; "
                "frame-ancestors 'none'; form-action 'self'",
            )
        else:
            response.setdefault(
                "Content-Security-Policy",
                "default-src 'self'; img-src 'self' data:; "
                "style-src 'self' 'unsafe-inline'; script-src 'self'; "
                "font-src 'self'; object-src 'none'; base-uri 'self'; "
                "frame-ancestors 'none'; form-action 'self'",
            )
        return response
