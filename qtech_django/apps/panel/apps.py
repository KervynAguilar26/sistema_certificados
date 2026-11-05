"""Configuración de la aplicación del panel."""

from __future__ import annotations

from django.apps import AppConfig


class PanelConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.panel"
    verbose_name = "Panel operativo"
