"""Crea el contenido inicial del sitio y del sistema de certificados."""

from __future__ import annotations

from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.certificates.models import CertificateTemplate, CertificateType
from apps.core.models import (
    GalleryImage,
    HeroSlide,
    Service,
    SiteSettings,
    TeamMember,
)

STATIC_IMG = Path(settings.BASE_DIR) / "static" / "img"


def _attach_image(instance, field_name: str, filename: str) -> bool:
    """Asigna una imagen de ``static/img`` si el campo está vacío."""

    field = getattr(instance, field_name)
    if field:
        return False
    source = STATIC_IMG / filename
    if not source.exists():
        return False
    with source.open("rb") as handle:
        field.save(filename, File(handle), save=False)
    return True


class Command(BaseCommand):
    help = (
        "Crea la configuración del sitio, tipos de certificado, servicios, "
        "equipo, galería y diapositivas iniciales. Es seguro ejecutarlo varias veces."
    )

    @transaction.atomic
    def handle(self, *args, **options):
        created = []

        # ------------------------------------------------------------------
        # Configuración del sitio
        # ------------------------------------------------------------------
        site = SiteSettings.load()
        changed = False
        if not site.logo:
            changed |= _attach_image(site, "logo", "logo.png")
        if not site.favicon:
            changed |= _attach_image(site, "favicon", "favicon.png")
        if changed:
            site.save()
        created.append("configuración del sitio")

        # ------------------------------------------------------------------
        # Tipos de certificado
        # ------------------------------------------------------------------
        compliance, type_created = CertificateType.objects.get_or_create(
            name_es="CERTIFICADO DE CUMPLIMIENTO",
            defaults={
                "name_en": "CERTIFICATE OF COMPLIANCE",
                "name_zh": "合格证书",
                "is_default": True,
            },
        )
        if type_created:
            created.append("tipo de certificado")

        # ------------------------------------------------------------------
        # Plantilla HTML predeterminada
        # ------------------------------------------------------------------
        if not CertificateTemplate.objects.exists():
            template_path = (
                Path(__file__).resolve().parents[3]
                / "certificates"
                / "templates"
                / "certificates"
                / "default_certificate.html"
            )
            if template_path.exists():
                content = template_path.read_text(encoding="utf-8")
                template = CertificateTemplate(
                    name="Plantilla institucional",
                    description=(
                        "Plantilla A4 con marco dorado, código QR y anexo de modelos. "
                        "Puede editarla o subir su propia plantilla HTML."
                    ),
                    content=content,
                    is_default=True,
                )
                try:
                    template.full_clean()
                except Exception as exc:  # pragma: no cover - defensa
                    self.stderr.write(
                        self.style.WARNING(
                            f"No se pudo validar la plantilla inicial: {exc}"
                        )
                    )
                else:
                    template.save()
                    created.append("plantilla de certificado")

        # ------------------------------------------------------------------
        # Servicios
        # ------------------------------------------------------------------
        services = [
            (
                "Laboratory technical testing",
                "Mechanical, electronic and safety tests performed under "
                "international standards and controlled laboratory conditions.",
                "bi bi-speedometer",
                10,
            ),
            (
                "Metrology and calibration",
                "High-precision measurement, equipment calibration and "
                "traceability for industrial instruments.",
                "bi bi-cpu",
                20,
            ),
            (
                "Certification and homologation",
                "Compliance assessment and certificate issuance for products "
                "that must meet regulated market requirements.",
                "bi bi-file-earmark-check",
                30,
            ),
        ]
        for title, description, icon, order in services:
            _, was_created = Service.objects.get_or_create(
                title=title,
                defaults={
                    "description": description,
                    "icon": icon,
                    "order": order,
                    "is_active": True,
                },
            )
            if was_created:
                created.append(f"servicio: {title}")

        # ------------------------------------------------------------------
        # Equipo
        # ------------------------------------------------------------------
        director, was_created = TeamMember.objects.get_or_create(
            name="Li Fang",
            defaults={
                "role": "Director / Chief Engineer",
                "bio": (
                    "Leads the technical and certification team with more than "
                    "twenty years of experience in industrial testing."
                ),
                "order": 10,
                "is_active": True,
            },
        )
        if was_created:
            _attach_image(director, "photo", "director.jpg")
            director.save()
            created.append("miembro del equipo")

        # ------------------------------------------------------------------
        # Galería
        # ------------------------------------------------------------------
        if not GalleryImage.objects.exists():
            gallery = [
                ("Laboratory facilities", "slide1.jpg", 10),
                ("Testing equipment", "slide2.jpg", 20),
                ("Certification process", "slide3.jpg", 30),
            ]
            for title, filename, order in gallery:
                image = GalleryImage(
                    title=title,
                    alt_text=title,
                    order=order,
                    is_active=True,
                )
                if _attach_image(image, "image", filename):
                    image.save()
                    created.append(f"imagen de galería: {title}")

        # ------------------------------------------------------------------
        # Diapositivas principales
        # ------------------------------------------------------------------
        if not HeroSlide.objects.exists():
            slides = [
                (
                    "Technical testing and certification specialists",
                    "Precision, compliance and international quality standards.",
                    "slide1.jpg",
                    "Explore our services",
                    "#servicios",
                    10,
                ),
                (
                    "Accredited laboratory and metrology services",
                    "High-precision diagnostics for mechanical and electronic equipment.",
                    "slide2.jpg",
                    "Request an assessment",
                    "#contacto",
                    20,
                ),
                (
                    "Certificates with public online verification",
                    "Every document includes a secure QR code and a unique verification token.",
                    "slide3.jpg",
                    "Verify a certificate",
                    "/verify/",
                    30,
                ),
            ]
            for title, subtitle, filename, cta_label, cta_url, order in slides:
                slide = HeroSlide(
                    title=title,
                    subtitle=subtitle,
                    alt_text=title,
                    cta_label=cta_label,
                    cta_url=cta_url,
                    order=order,
                    is_active=True,
                )
                if _attach_image(slide, "image", filename):
                    slide.save()
                    created.append(f"diapositiva: {title}")

        self.stdout.write(self.style.SUCCESS("Contenido inicial creado/verificado:"))
        for item in created:
            self.stdout.write(f"  - {item}")
        self.stdout.write(
            self.style.SUCCESS(
                "Puede iniciar sesión en el panel privado y editar todo el contenido."
            )
        )
