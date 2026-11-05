"""Importa usuarios y certificados desde la base de datos del sistema PHP."""

from __future__ import annotations

import os
from datetime import date, datetime

import psycopg
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.certificates.models import Certificate, CertificateType, _split_models


def _env(name: str, default: str) -> str:
    return os.environ.get(name, default)


def _parse_bool(value) -> bool:
    return str(value or "").strip().upper() in {"SI", "SÍ", "YES", "TRUE", "1"}


def _parse_date(value) -> date | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def _parse_datetime(value):
    if not value or not isinstance(value, datetime):
        return None
    if timezone.is_naive(value):
        return timezone.make_aware(value, timezone.get_current_timezone())
    return value


class Command(BaseCommand):
    help = (
        "Copia los usuarios y certificados de la base de datos PostgreSQL del "
        "sistema PHP anterior. Los hashes bcrypt se conservan y se actualizan a "
        "Argon2 en el siguiente inicio de sesión."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--legacy-db",
            default=_env("LEGACY_DB_NAME", "certificaciones_db"),
            help="Nombre de la base de datos antigua.",
        )
        parser.add_argument(
            "--legacy-host",
            default=_env("LEGACY_DB_HOST", "127.0.0.1"),
            help="Host de la base de datos antigua.",
        )
        parser.add_argument(
            "--legacy-port",
            default=_env("LEGACY_DB_PORT", "5432"),
            help="Puerto de la base de datos antigua.",
        )
        parser.add_argument(
            "--legacy-user",
            default=_env("LEGACY_DB_USER", "postgres"),
            help="Usuario de la base de datos antigua.",
        )
        parser.add_argument(
            "--legacy-password",
            default=_env("LEGACY_DB_PASSWORD", ""),
            help="Contraseña de la base de datos antigua.",
        )
        parser.add_argument(
            "--overwrite-passwords",
            action="store_true",
            help="Reemplaza las contraseñas locales con los hashes heredados.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Muestra lo que se importaría sin guardar cambios.",
        )

    def handle(self, *args, **options):
        connection_kwargs = {
            "host": options["legacy_host"],
            "port": options["legacy_port"],
            "dbname": options["legacy_db"],
            "user": options["legacy_user"],
            "password": options["legacy_password"],
            "connect_timeout": 10,
        }
        try:
            legacy = psycopg.connect(**connection_kwargs)
        except Exception as exc:
            raise CommandError(
                f"No se pudo conectar con la base de datos antigua: {exc}"
            ) from exc

        dry_run = options["dry_run"]
        users_created = 0
        users_updated = 0
        certificates_created = 0
        certificates_updated = 0
        user_map: dict[int, User] = {}

        try:
            with legacy.cursor() as cursor:
                cursor.execute("SELECT id, nombre, email, rol_id, activo, password_hash FROM usuarios ORDER BY id")
                legacy_users = cursor.fetchall()

                cursor.execute("SELECT id, codigo_certificado, tipo_certificado, token_verificacion, solicitante, fabricante, direccion_fabricante, producto, descripcion_producto, marcas, modelos_adjuntos, parametros_ensayo, normas_ensayo, reporte_ensayo, fecha_emision, fecha_expiracion, analista_id, estado, mostrar_parametros, creado_en FROM certificados ORDER BY id")
                legacy_certificates = cursor.fetchall()

            with transaction.atomic():
                # ----------------------------------------------------------
                # Usuarios
                # ----------------------------------------------------------
                for (
                    legacy_id,
                    nombre,
                    email,
                    rol_id,
                    activo,
                    password_hash,
                ) in legacy_users:
                    email = (email or "").strip().lower()
                    if not email:
                        self.stderr.write(
                            self.style.WARNING(
                                f"Usuario heredado {legacy_id} sin correo; se omite."
                            )
                        )
                        continue
                    role = (
                        User.Role.SUPERADMIN
                        if int(rol_id or 0) == 1
                        else User.Role.ANALYST
                    )
                    defaults = {
                        "full_name": (nombre or email)[:150],
                        "role": role,
                        "is_active": bool(activo),
                        "is_staff": True,
                        "is_superuser": role == User.Role.SUPERADMIN,
                    }
                    user = User.objects.filter(email=email).first()
                    if user is None:
                        user = User(email=email, **defaults)
                        if password_hash:
                            user.password = f"php_bcrypt${password_hash}"
                        else:
                            user.set_unusable_password()
                        if not dry_run:
                            user.save()
                        users_created += 1
                    else:
                        for key, value in defaults.items():
                            setattr(user, key, value)
                        if options["overwrite_passwords"] and password_hash:
                            user.password = f"php_bcrypt${password_hash}"
                        if not dry_run:
                            user.save()
                        users_updated += 1
                    user_map[legacy_id] = user

                # ----------------------------------------------------------
                # Certificados
                # ----------------------------------------------------------
                for row in legacy_certificates:
                    (
                        legacy_id,
                        code,
                        type_name,
                        token,
                        applicant,
                        manufacturer,
                        manufacturer_address,
                        product,
                        product_description,
                        brand,
                        models_raw,
                        test_parameters,
                        test_standards,
                        test_report,
                        issue_date,
                        expiry_date,
                        analyst_id,
                        status,
                        show_parameters,
                        created_at,
                    ) = row

                    code = (code or "").strip()
                    if not code:
                        self.stderr.write(
                            self.style.WARNING(
                                f"Certificado heredado {legacy_id} sin número; se omite."
                            )
                        )
                        continue

                    type_name = (type_name or "").strip()
                    certificate_type = None
                    if type_name:
                        certificate_type, _ = CertificateType.objects.get_or_create(
                            name_es=type_name,
                            defaults={
                                "name_en": (
                                    "CERTIFICATE OF COMPLIANCE"
                                    if "CUMPLIMIENTO" in type_name.upper()
                                    else type_name
                                ),
                                "name_zh": "合格证书"
                                if "CUMPLIMIENTO" in type_name.upper()
                                else "",
                            },
                        )

                    models = _split_models(models_raw or "")
                    issue = _parse_date(issue_date) or timezone.localdate()
                    expiry = _parse_date(expiry_date) or issue
                    certificate_status = (
                        Certificate.Status.BLOCKED
                        if str(status or "").strip().lower() == "bloqueado"
                        else Certificate.Status.ACTIVE
                    )
                    defaults = {
                        "certificate_type": certificate_type,
                        "token": (token or "").strip(),
                        "applicant": (applicant or "")[:200],
                        "manufacturer": (manufacturer or "")[:200],
                        "manufacturer_address": manufacturer_address or "",
                        "product": (product or "")[:200],
                        "product_description": product_description or "",
                        "brand": (brand or "")[:200],
                        "models_text": ", ".join(models),
                        "test_parameters": test_parameters or "",
                        "show_parameters": _parse_bool(show_parameters),
                        "test_standards": test_standards or "",
                        "test_report": (test_report or "")[:150],
                        "issue_date": issue,
                        "expiry_date": expiry,
                        "status": certificate_status,
                        "analyst": user_map.get(analyst_id),
                    }
                    certificate = Certificate.objects.filter(code=code).first()
                    if certificate is None:
                        certificate = Certificate(code=code, **defaults)
                        if not certificate.token:
                            certificate.token = Certificate._meta.get_field(
                                "token"
                            ).get_default()
                        if not dry_run:
                            certificate.save()
                            created_value = _parse_datetime(created_at)
                            if created_value:
                                Certificate.objects.filter(pk=certificate.pk).update(
                                    created_at=created_value
                                )
                        certificates_created += 1
                    else:
                        for key, value in defaults.items():
                            if key == "token" and not value:
                                continue
                            setattr(certificate, key, value)
                        if not dry_run:
                            certificate.save()
                            created_value = _parse_datetime(created_at)
                            if created_value:
                                Certificate.objects.filter(pk=certificate.pk).update(
                                    created_at=created_value
                                )
                        certificates_updated += 1

                if dry_run:
                    transaction.set_rollback(True)
        finally:
            legacy.close()

        prefix = "Simulación: " if dry_run else ""
        self.stdout.write(
            self.style.SUCCESS(
                f"{prefix}usuarios creados: {users_created}, actualizados: {users_updated}; "
                f"certificados creados: {certificates_created}, actualizados: {certificates_updated}."
            )
        )
        if users_created:
            self.stdout.write(
                "Los usuarios heredados conservan su contraseña PHP bcrypt y se "
                "migrarán a Argon2 en el próximo inicio de sesión."
            )
