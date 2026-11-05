"""Modelos de la web pública.

Todos los textos de ayuda y etiquetas de los formularios están en español, tal
como se solicitó para la captura de datos. La interfaz administrativa se
traduce a chino e inglés mediante ``QTechAdminSite``.
"""

from __future__ import annotations

from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils import timezone


def _image_help(text: str) -> str:
    return f"{text} Formatos: JPG, PNG o WebP. Tamaño máximo: 10 MB."


class SiteSettings(models.Model):
    """Configuración global editable por el propietario del sitio."""

    site_name = models.CharField(
        "Nombre de la institución",
        max_length=200,
        default="Qingdao Technology Engineering Institute",
        help_text="Nombre mostrado en la web, el pie de página y los certificados.",
    )
    tagline = models.CharField(
        "Lema",
        max_length=250,
        blank=True,
        default="Especialistas en Pruebas Técnicas y Certificación de Equipos",
        help_text="Frase corta mostrada bajo el nombre.",
    )
    address = models.TextField(
        "Dirección",
        blank=True,
        default=(
            "South 84 Building A, No. 1540 Jiushui Road, Laoshan District, "
            "Qingdao City, Shandong Province, China"
        ),
        help_text="Dirección completa mostrada en el pie de página.",
    )
    email = models.EmailField(
        "Correo electrónico",
        blank=True,
        default="info@qtecheni.com",
        help_text="Correo de contacto mostrado en la web.",
    )
    phone = models.CharField(
        "Teléfono",
        max_length=60,
        blank=True,
        help_text="Teléfono de contacto mostrado en la web.",
    )
    website = models.CharField(
        "Sitio web",
        max_length=120,
        blank=True,
        default="qtecheni.com",
        help_text="Dominio sin protocolo, por ejemplo qtecheni.com.",
    )
    director_name = models.CharField(
        "Nombre del director",
        max_length=120,
        blank=True,
        default="Li Fang",
        help_text="Nombre mostrado en la sección del equipo.",
    )

    logo = models.ImageField(
        "Logotipo",
        upload_to="site/",
        blank=True,
        help_text=_image_help("Recomendado: 512 x 512 px, PNG con transparencia."),
    )
    favicon = models.ImageField(
        "Favicon",
        upload_to="site/",
        blank=True,
        help_text=_image_help("Recomendado: 64 x 64 px, PNG."),
    )

    about_text = models.TextField(
        "Texto de la sección Nosotros",
        blank=True,
        default=(
            "Nos especializamos en la ejecución de pruebas técnicas y normativas "
            "a equipos e instrumentos mecánicos y electrónicos. Contamos con "
            "laboratorios equipados con tecnología de punta y personal de "
            "ingeniería con amplia trayectoria, garantizando la homologación y "
            "seguridad de la maquinaria de nuestros clientes."
        ),
        help_text="Párrafo principal de la sección Nosotros.",
    )
    about_badge_title = models.CharField(
        "Título del distintivo de cumplimiento",
        max_length=150,
        blank=True,
        default="Certificación CE garantizada",
        help_text="Título del mensaje destacado de cumplimiento.",
    )
    about_badge_text = models.CharField(
        "Texto del distintivo de cumplimiento",
        max_length=250,
        blank=True,
        default="Cumplimiento estricto de parámetros internacionales.",
        help_text="Texto del mensaje destacado de cumplimiento.",
    )

    hero_default_title = models.CharField(
        "Título principal por defecto",
        max_length=200,
        blank=True,
        help_text="Se usa si no hay diapositivas activas.",
    )
    hero_default_subtitle = models.TextField(
        "Subtítulo principal por defecto",
        blank=True,
        help_text="Se usa si no hay diapositivas activas.",
    )

    meta_title = models.CharField(
        "Título SEO",
        max_length=200,
        blank=True,
        help_text="Título del navegador para la página principal.",
    )
    meta_description = models.CharField(
        "Descripción SEO",
        max_length=160,
        blank=True,
        help_text="Descripción para buscadores (máx. 160 caracteres).",
    )

    social_facebook = models.URLField("Facebook", blank=True)
    social_linkedin = models.URLField("LinkedIn", blank=True)
    social_instagram = models.URLField("Instagram", blank=True)
    social_youtube = models.URLField("YouTube", blank=True)

    updated_at = models.DateTimeField("Actualizado el", auto_now=True)

    class Meta:
        verbose_name = "Configuración del sitio"
        verbose_name_plural = "Configuración del sitio"

    def __str__(self) -> str:
        return self.site_name

    def save(self, *args, **kwargs):
        # Registro único: siempre pk=1.
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls) -> "SiteSettings":
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class HeroSlide(models.Model):
    title = models.CharField("Título", max_length=200)
    subtitle = models.TextField("Subtítulo", blank=True)
    image = models.ImageField(
        "Imagen",
        upload_to="hero/",
        help_text=_image_help("Recomendado: 1920 x 1080 px (16:9)."),
    )
    alt_text = models.CharField(
        "Texto alternativo",
        max_length=200,
        blank=True,
        help_text="Describe la imagen para accesibilidad.",
    )
    cta_label = models.CharField(
        "Texto del botón",
        max_length=80,
        blank=True,
        help_text="Déjelo vacío para ocultar el botón.",
    )
    cta_url = models.CharField(
        "Enlace del botón",
        max_length=200,
        blank=True,
        help_text="Por ejemplo #servicios o /verify/.",
    )
    order = models.PositiveIntegerField("Orden", default=0)
    is_active = models.BooleanField("Activo", default=True)
    created_at = models.DateTimeField("Creado el", auto_now_add=True)

    class Meta:
        verbose_name = "Diapositiva principal"
        verbose_name_plural = "Diapositivas principales"
        ordering = ("order", "id")

    def __str__(self) -> str:
        return self.title


class Service(models.Model):
    title = models.CharField("Título", max_length=150)
    description = models.TextField("Descripción")
    icon = models.CharField(
        "Icono",
        max_length=80,
        blank=True,
        default="bi bi-gear",
        help_text="Clase de Bootstrap Icons, por ejemplo bi bi-cpu.",
    )
    order = models.PositiveIntegerField("Orden", default=0)
    is_active = models.BooleanField("Activo", default=True)

    class Meta:
        verbose_name = "Servicio"
        verbose_name_plural = "Servicios"
        ordering = ("order", "id")

    def __str__(self) -> str:
        return self.title


class TeamMember(models.Model):
    name = models.CharField("Nombre", max_length=150)
    role = models.CharField(
        "Cargo",
        max_length=150,
        blank=True,
        help_text="Cargo mostrado bajo el nombre.",
    )
    bio = models.TextField(
        "Biografía",
        blank=True,
        help_text="Biografía breve.",
    )
    photo = models.ImageField(
        "Fotografía",
        upload_to="team/",
        blank=True,
        help_text=_image_help("Recomendado: 600 x 600 px (cuadrada)."),
    )
    order = models.PositiveIntegerField("Orden", default=0)
    is_active = models.BooleanField("Activo", default=True)

    class Meta:
        verbose_name = "Miembro del equipo"
        verbose_name_plural = "Equipo"
        ordering = ("order", "id")

    def __str__(self) -> str:
        return self.name


class GalleryImage(models.Model):
    title = models.CharField("Título", max_length=150, blank=True)
    image = models.ImageField(
        "Imagen",
        upload_to="gallery/",
        help_text=_image_help("Recomendado: 1200 x 800 px (3:2)."),
    )
    alt_text = models.CharField(
        "Texto alternativo",
        max_length=200,
        blank=True,
        help_text="Describe la imagen para accesibilidad.",
    )
    order = models.PositiveIntegerField("Orden", default=0)
    is_active = models.BooleanField("Activo", default=True)

    class Meta:
        verbose_name = "Imagen de galería"
        verbose_name_plural = "Galería"
        ordering = ("order", "id")

    def __str__(self) -> str:
        return self.title or f"Imagen {self.pk}"


class ContactMessage(models.Model):
    name = models.CharField("Nombre", max_length=150)
    email = models.EmailField("Correo electrónico")
    phone = models.CharField("Teléfono", max_length=60, blank=True)
    company = models.CharField("Empresa", max_length=150, blank=True)
    message = models.TextField("Mensaje")
    is_read = models.BooleanField("Leído", default=False)
    ip_address = models.GenericIPAddressField("Dirección IP", blank=True, null=True)
    user_agent = models.CharField("Navegador", max_length=300, blank=True)
    created_at = models.DateTimeField("Recibido el", default=timezone.now)

    class Meta:
        verbose_name = "Mensaje de contacto"
        verbose_name_plural = "Mensajes de contacto"
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.name} <{self.email}>"
