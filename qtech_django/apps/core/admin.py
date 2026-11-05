"""Registro de la web pública en el panel administrativo."""

from __future__ import annotations

from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils import translation

from .i18n import normalize_lang, tr_admin
from .models import (
    ContactMessage,
    GalleryImage,
    HeroSlide,
    Service,
    SiteSettings,
    TeamMember,
)


def _image_preview(obj, field_name: str, height: int = 60):
    field = getattr(obj, field_name)
    if not field:
        return "—"
    try:
        url = field.url
    except Exception:
        return "—"
    return format_html(
        '<img src="{}" alt="" style="height:{}px;width:auto;border-radius:6px;'
        'object-fit:cover;" />',
        url,
        height,
    )


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ("site_name", "email", "website", "updated_at")
    readonly_fields = ("updated_at", "logo_preview", "favicon_preview")
    fieldsets = (
        (
            "General",
            {
                "fields": (
                    "site_name",
                    "tagline",
                    "director_name",
                    "website",
                    "updated_at",
                )
            },
        ),
        (
            "Contacto",
            {"fields": ("address", "email", "phone")},
        ),
        (
            "Imágenes",
            {
                "fields": (
                    "logo",
                    "logo_preview",
                    "favicon",
                    "favicon_preview",
                ),
                "description": (
                    "Logotipo: 512 x 512 px, PNG con transparencia. "
                    "Favicon: 64 x 64 px, PNG."
                ),
            },
        ),
        (
            "Página principal",
            {
                "fields": (
                    "hero_default_title",
                    "hero_default_subtitle",
                    "about_text",
                    "about_badge_title",
                    "about_badge_text",
                )
            },
        ),
        (
            "SEO",
            {"fields": ("meta_title", "meta_description")},
        ),
        (
            "Redes sociales",
            {
                "fields": (
                    "social_facebook",
                    "social_linkedin",
                    "social_instagram",
                    "social_youtube",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(description="Vista previa del logotipo")
    def logo_preview(self, obj):
        return _image_preview(obj, "logo", 90)

    @admin.display(description="Vista previa del favicon")
    def favicon_preview(self, obj):
        return _image_preview(obj, "favicon", 48)

    def response_add(self, request, obj, post_url_continue=None):
        return self.response_post_save_add(request, obj)

    def changelist_view(self, request, extra_context=None):
        obj = SiteSettings.load()
        url = reverse("admin:core_sitesettings_change", args=[obj.pk])
        from django.shortcuts import redirect

        return redirect(url)


@admin.register(HeroSlide)
class HeroSlideAdmin(admin.ModelAdmin):
    list_display = ("title", "order", "is_active", "preview")
    list_editable = ("order", "is_active")
    list_filter = ("is_active",)
    search_fields = ("title", "subtitle")
    readonly_fields = ("preview",)

    @admin.display(description="Vista previa")
    def preview(self, obj):
        return _image_preview(obj, "image", 70)


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("title", "order", "is_active")
    list_editable = ("order", "is_active")
    list_filter = ("is_active",)
    search_fields = ("title", "description")


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ("name", "role", "order", "is_active", "preview")
    list_editable = ("order", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "role", "bio")
    readonly_fields = ("preview",)

    @admin.display(description="Fotografía")
    def preview(self, obj):
        return _image_preview(obj, "photo", 60)


@admin.register(GalleryImage)
class GalleryImageAdmin(admin.ModelAdmin):
    list_display = ("__str__", "order", "is_active", "preview")
    list_editable = ("order", "is_active")
    list_filter = ("is_active",)
    search_fields = ("title", "alt_text")
    readonly_fields = ("preview",)

    @admin.display(description="Vista previa")
    def preview(self, obj):
        return _image_preview(obj, "image", 60)


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "company", "is_read", "created_at")
    list_filter = ("is_read", "created_at")
    search_fields = ("name", "email", "company", "message")
    readonly_fields = (
        "name",
        "email",
        "phone",
        "company",
        "message",
        "ip_address",
        "user_agent",
        "created_at",
    )
    actions = ("mark_read", "mark_unread")
    date_hierarchy = "created_at"

    def has_add_permission(self, request):
        return False

    def get_actions(self, request):
        actions = super().get_actions(request)
        lang = normalize_lang(translation.get_language(), admin=True)
        if "mark_read" in actions:
            func, name, _ = actions["mark_read"]
            actions["mark_read"] = (func, name, tr_admin("admin_mark_read", lang))
        if "mark_unread" in actions:
            func, name, _ = actions["mark_unread"]
            actions["mark_unread"] = (func, name, tr_admin("admin_mark_unread", lang))
        return actions

    @admin.action(description="Marcar como leído")
    def mark_read(self, request, queryset):
        queryset.update(is_read=True)

    @admin.action(description="Marcar como no leído")
    def mark_unread(self, request, queryset):
        queryset.update(is_read=False)
