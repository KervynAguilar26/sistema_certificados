"""AppConfig del panel administrativo con sitio personalizado."""

from django.contrib.admin.apps import AdminConfig


class QTechAdminConfig(AdminConfig):
    default_site = "apps.core.admin_site.QTechAdminSite"
