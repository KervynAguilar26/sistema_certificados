"""URLs raíz del proyecto."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from apps.core.views import health, robots_txt, set_language

urlpatterns = [
    path("", include("apps.core.urls")),
    path("verify/", include("apps.certificates.urls")),
    path("i18n/set-language/", set_language, name="set_language"),
    path("health/", health, name="health"),
    path("robots.txt", robots_txt, name="robots_txt"),
    path("panel/", include("apps.panel.urls")),
    path(settings.ADMIN_URL_PATH, admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
