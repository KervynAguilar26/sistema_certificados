"""Pruebas del sistema de certificados."""

from __future__ import annotations

import unittest
from datetime import timedelta
from unittest.mock import patch

from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User
from apps.core.models import SiteSettings

from .forms import CertificateAdminForm, CertificateTemplateAdminForm
from .models import (
    Certificate,
    CertificateEvent,
    CertificateTemplate,
    CertificateType,
    ValidationLog,
)
from .pdf import PDFRenderError, pdf_backend_available, render_certificate_pdf
from .rendering import TemplateRenderError, default_template_source, render_certificate_html
from .security import MAX_TEMPLATE_BYTES, validate_certificate_template


class SecurityTests(TestCase):
    def test_default_template_is_allowed(self):
        validate_certificate_template(default_template_source())

    def test_rejects_script_tags(self):
        with self.assertRaises(ValidationError):
            validate_certificate_template("<html><script>alert(1)</script></html>")

    def test_rejects_iframe_and_form_tags(self):
        for source in (
            '<iframe src="https://example.com"></iframe>',
            '<form action="/x"></form>',
            '<object data="x"></object>',
        ):
            with self.assertRaises(ValidationError):
                validate_certificate_template(source)

    def test_rejects_event_handlers(self):
        with self.assertRaises(ValidationError):
            validate_certificate_template('<div onclick="alert(1)">x</div>')

    def test_rejects_javascript_urls(self):
        with self.assertRaises(ValidationError):
            validate_certificate_template('<a href="javascript:alert(1)">x</a>')

    def test_rejects_unknown_template_tags(self):
        with self.assertRaises(ValidationError):
            validate_certificate_template("{% include 'x.html' %}")

    def test_rejects_unknown_filters(self):
        with self.assertRaises(ValidationError):
            validate_certificate_template("{{ applicant|safe }}")

    def test_rejects_reserved_variables(self):
        with self.assertRaises(ValidationError):
            validate_certificate_template("{{ user.email }}")

    def test_rejects_external_css_urls(self):
        with self.assertRaises(ValidationError):
            validate_certificate_template(
                "<style>.x{background:url(https://evil.example/x.png)}</style>"
            )

    def test_rejects_oversized_templates(self):
        with self.assertRaises(ValidationError):
            validate_certificate_template("x" * (MAX_TEMPLATE_BYTES + 1))


@override_settings(SITE_BASE_URL="https://certificates.example.test")
class CertificateBaseTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.superadmin = User.objects.create_superuser(
            email="admin@example.test",
            password="AdminPassword123!",
            full_name="Administrator",
        )
        cls.analyst = User.objects.create_user(
            email="analyst@example.test",
            password="AnalystPassword123!",
            full_name="Analyst",
        )
        cls.certificate_type = CertificateType.objects.create(
            name_es="Certificado CE",
            name_en="CE Certificate",
            name_zh="CE 证书",
            is_default=True,
        )
        cls.template = CertificateTemplate.objects.create(
            name="Default",
            content=default_template_source(),
            is_default=True,
        )
        cls.certificate = Certificate.objects.create(
            code="TEST-CERT-001",
            certificate_type=cls.certificate_type,
            applicant="Example Trading Company",
            manufacturer="Example Manufacturer",
            manufacturer_address="1 Example Road, Qingdao",
            product="Example product",
            product_description="A product used for automated tests.",
            brand="EXAMPLE",
            models_text="M1, M2, M3",
            test_parameters="Parameter A: 1",
            test_standards="ISO 9001:2015",
            test_report="REPORT-001",
            issue_date=timezone.localdate(),
            expiry_date=timezone.localdate() + timedelta(days=365),
            status=Certificate.Status.ACTIVE,
            template=cls.template,
        )

    def setUp(self):
        cache.clear()


class RenderingTests(CertificateBaseTests):
    def test_renders_certificate_with_data_and_qr(self):
        html = render_certificate_html(self.certificate, lang="en")
        self.assertIn("TEST-CERT-001", html)
        self.assertIn("Example Trading Company", html)
        self.assertIn("data:image/png;base64,", html)
        self.assertIn("data:image/", html)

    def test_html_escapes_untrusted_certificate_data(self):
        self.certificate.applicant = "<script>alert(1)</script>"
        self.certificate.save(update_fields=["applicant"])
        html = render_certificate_html(self.certificate, lang="en")
        self.assertNotIn("<script>alert(1)</script>", html)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", html)

    def test_large_model_list_creates_annex_pages(self):
        self.certificate.models_text = ", ".join(f"MODEL-{i}" for i in range(400))
        self.certificate.save(update_fields=["models_text"])
        html = render_certificate_html(self.certificate, lang="en")
        self.assertIn("MODEL-399", html)
        # 400 modelos => 3 páginas de anexo además de la principal.
        self.assertIn("04", html)

    def test_invalid_stored_template_raises_controlled_error(self):
        self.template.content = "{% debug %}"
        self.template.save(update_fields=["content", "updated_at"])
        with self.assertRaises(TemplateRenderError):
            render_certificate_html(self.certificate, lang="en")

    def test_spanish_certificate_uses_spanish_type_and_labels(self):
        html = render_certificate_html(self.certificate, lang="es")
        self.assertIn("Certificado CE", html)
        self.assertIn("Solicitante", html)
        self.assertIn("Example Trading Company", html)


class PublicVerificationTests(CertificateBaseTests):
    def test_valid_certificate_by_code(self):
        response = self.client.get(
            reverse("certificates:verify"), {"q": self.certificate.code, "lang": "en"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["result"], "valid")
        self.assertContains(response, "TEST-CERT-001")

    def test_valid_certificate_by_token(self):
        response = self.client.get(
            reverse("certificates:verify"), {"token": self.certificate.token}
        )
        self.assertEqual(response.context["result"], "valid")

    def test_code_lookup_is_case_insensitive(self):
        response = self.client.get(
            reverse("certificates:verify"), {"q": self.certificate.code.lower()}
        )
        self.assertEqual(response.context["result"], "valid")

    def test_unknown_certificate_is_not_found(self):
        response = self.client.get(
            reverse("certificates:verify"), {"q": "DOES-NOT-EXIST"}
        )
        self.assertEqual(response.context["result"], "not_found")
        self.assertTrue(
            ValidationLog.objects.filter(result=ValidationLog.Result.NOT_FOUND).exists()
        )

    def test_blocked_certificate_is_reported(self):
        self.certificate.status = Certificate.Status.BLOCKED
        self.certificate.save(update_fields=["status"])
        response = self.client.get(
            reverse("certificates:verify"), {"q": self.certificate.code}
        )
        self.assertEqual(response.context["result"], "blocked")

    def test_expired_certificate_is_reported(self):
        self.certificate.expiry_date = timezone.localdate() - timedelta(days=1)
        self.certificate.save(update_fields=["expiry_date"])
        response = self.client.get(
            reverse("certificates:verify"), {"q": self.certificate.code}
        )
        self.assertEqual(response.context["result"], "expired")

    def test_rate_limit_blocks_repeated_attempts(self):
        with patch("apps.certificates.views.RATE_LIMIT_ATTEMPTS", 2):
            for _ in range(2):
                self.client.get(
                    reverse("certificates:verify"), {"q": self.certificate.code}
                )
            response = self.client.get(
                reverse("certificates:verify"), {"q": self.certificate.code}
            )
        self.assertEqual(response.context["result"], "rate_limited")
        self.assertTrue(
            ValidationLog.objects.filter(
                result=ValidationLog.Result.RATE_LIMITED
            ).exists()
        )

    def test_validation_attempt_is_logged(self):
        self.client.get(reverse("certificates:verify"), {"q": self.certificate.code})
        log = ValidationLog.objects.latest("created_at")
        self.assertEqual(log.certificate, self.certificate)
        self.assertTrue(log.success)


class AdminTests(CertificateBaseTests):
    def test_admin_requires_login(self):
        response = self.client.get(reverse("admin:index"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("admin:login"), response["Location"])

    def test_superadmin_can_open_certificate_admin(self):
        self.client.force_login(self.superadmin)
        urls = [
            reverse("admin:index"),
            reverse("admin:certificates_certificate_changelist"),
            reverse(
                "admin:certificates_certificate_change", args=[self.certificate.pk]
            ),
            reverse(
                "admin:certificates_certificatetemplate_change", args=[self.template.pk]
            ),
            reverse(
                "admin:certificates_certificatetemplate_preview",
                args=[self.template.pk, "en"],
            ),
        ]
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_template_change_page_lists_placeholders(self):
        self.client.force_login(self.superadmin)
        response = self.client.get(
            reverse(
                "admin:certificates_certificatetemplate_change", args=[self.template.pk]
            )
        )
        self.assertContains(response, "placeholders_help")
        self.assertContains(response, "models_display")

    def test_analyst_can_manage_certificates_but_not_users(self):
        self.client.force_login(self.analyst)
        self.assertEqual(
            self.client.get(
                reverse("admin:certificates_certificate_changelist")
            ).status_code,
            200,
        )
        self.assertEqual(
            self.client.get(reverse("admin:accounts_user_changelist")).status_code, 403
        )

    def test_certificate_qr_view_returns_png(self):
        self.client.force_login(self.superadmin)
        response = self.client.get(
            reverse("admin:certificates_certificate_qr", args=[self.certificate.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "image/png")
        self.assertTrue(response.content.startswith(b"\x89PNG"))

    def test_template_preview_uses_sample_certificate(self):
        self.client.force_login(self.superadmin)
        response = self.client.get(
            reverse(
                "admin:certificates_certificatetemplate_preview",
                args=[self.template.pk, "zh-hans"],
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "SAMPLE-0001")

    def test_superadmin_can_open_all_admin_sections(self):
        self.client.force_login(self.superadmin)
        CertificateEvent.objects.create(
            certificate=self.certificate,
            user=self.superadmin,
            event=CertificateEvent.Event.CREATED,
        )
        ValidationLog.objects.create(
            query=self.certificate.code,
            result=ValidationLog.Result.VALID,
            success=True,
            certificate=self.certificate,
        )
        urls = [
            reverse("admin:core_sitesettings_change", args=[SiteSettings.load().pk]),
            reverse("admin:core_heroslide_changelist"),
            reverse("admin:core_service_changelist"),
            reverse("admin:core_teammember_changelist"),
            reverse("admin:core_galleryimage_changelist"),
            reverse("admin:core_contactmessage_changelist"),
            reverse("admin:accounts_user_changelist"),
            reverse("admin:accounts_user_change", args=[self.analyst.pk]),
            reverse("admin:certificates_certificateevent_changelist"),
            reverse("admin:certificates_validationlog_changelist"),
            reverse("admin:certificates_certificatetype_changelist"),
        ]
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_bulk_status_actions_update_certificates(self):
        self.client.force_login(self.superadmin)
        changelist = reverse("admin:certificates_certificate_changelist")

        self.client.post(
            changelist,
            {"action": "mark_blocked", "_selected_action": [self.certificate.pk]},
        )
        self.certificate.refresh_from_db()
        self.assertEqual(self.certificate.status, Certificate.Status.BLOCKED)

        self.client.post(
            changelist,
            {"action": "mark_active", "_selected_action": [self.certificate.pk]},
        )
        self.certificate.refresh_from_db()
        self.assertEqual(self.certificate.status, Certificate.Status.ACTIVE)

    def test_bulk_regenerate_tokens_changes_token(self):
        self.client.force_login(self.superadmin)
        old_token = self.certificate.token
        self.client.post(
            reverse("admin:certificates_certificate_changelist"),
            {
                "action": "regenerate_tokens",
                "_selected_action": [self.certificate.pk],
            },
        )
        self.certificate.refresh_from_db()
        self.assertNotEqual(self.certificate.token, old_token)
        self.assertTrue(
            CertificateEvent.objects.filter(
                certificate=self.certificate,
                event=CertificateEvent.Event.TOKEN_REGENERATED,
            ).exists()
        )

    def test_models_csv_template_is_downloadable(self):
        self.client.force_login(self.superadmin)
        response = self.client.get(
            reverse("admin:certificates_certificate_models_csv_template")
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/csv", response["Content-Type"])
        self.assertIn("MODELO-001", response.content.decode("utf-8"))

    def test_regenerate_token_view_requires_post_and_changes_token(self):
        self.client.force_login(self.superadmin)
        url = reverse(
            "admin:certificates_certificate_regenerate_token",
            args=[self.certificate.pk],
        )
        self.assertEqual(self.client.get(url).status_code, 405)
        old_token = self.certificate.token
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.certificate.refresh_from_db()
        self.assertNotEqual(self.certificate.token, old_token)


class PDFExportTests(CertificateBaseTests):
    def test_pdf_view_returns_pdf_and_logs_event(self):
        self.client.force_login(self.superadmin)
        with patch(
            "apps.certificates.admin.render_certificate_pdf",
            return_value=b"%PDF-1.7 test",
        ):
            response = self.client.get(
                reverse(
                    "admin:certificates_certificate_pdf",
                    args=[self.certificate.pk, "es"],
                )
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn("inline", response["Content-Disposition"])
        self.assertTrue(response.content.startswith(b"%PDF"))
        self.assertTrue(
            CertificateEvent.objects.filter(
                certificate=self.certificate,
                event=CertificateEvent.Event.PDF_DOWNLOADED,
            ).exists()
        )

    def test_pdf_download_forces_attachment(self):
        self.client.force_login(self.superadmin)
        with patch(
            "apps.certificates.admin.render_certificate_pdf",
            return_value=b"%PDF-1.7 test",
        ):
            response = self.client.get(
                reverse(
                    "admin:certificates_certificate_pdf",
                    args=[self.certificate.pk, "en"],
                ),
                {"download": "1"},
            )
        self.assertIn("attachment", response["Content-Disposition"])

    def test_pdf_view_reports_missing_backend(self):
        self.client.force_login(self.superadmin)
        with patch(
            "apps.certificates.admin.render_certificate_pdf",
            side_effect=PDFRenderError("sin backend"),
        ):
            response = self.client.get(
                reverse(
                    "admin:certificates_certificate_pdf",
                    args=[self.certificate.pk, "en"],
                )
            )
        self.assertEqual(response.status_code, 302)

    @unittest.skipUnless(
        pdf_backend_available(), "WeasyPrint no está disponible en este equipo"
    )
    def test_real_pdf_generation(self):
        pdf = render_certificate_pdf(self.certificate, lang="es")
        self.assertTrue(pdf.startswith(b"%PDF"))


class FormTests(CertificateBaseTests):
    def _certificate_data(self, **overrides):
        data = {
            "code": "CSV-CERT-001",
            "applicant": "CSV Applicant",
            "product": "CSV Product",
            "issue_date": timezone.localdate().isoformat(),
            "expiry_date": (timezone.localdate() + timedelta(days=365)).isoformat(),
            "status": Certificate.Status.ACTIVE,
            "show_parameters": "on",
        }
        data.update(overrides)
        return data

    def test_csv_upload_replaces_models_text(self):
        upload = SimpleUploadedFile(
            "models.csv",
            b"Model A\nModel B\nModel A\n",
            content_type="text/csv",
        )
        form = CertificateAdminForm(
            data=self._certificate_data(models_text="Old model"),
            files={"models_csv": upload},
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["models_text"], "Model A, Model B")

    def test_template_upload_validates_and_sets_content(self):
        source = default_template_source()
        upload = SimpleUploadedFile(
            "template.html", source.encode("utf-8"), content_type="text/html"
        )
        form = CertificateTemplateAdminForm(
            data={"name": "Uploaded template", "description": ""},
            files={"file": upload},
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["content"], source)

    def test_template_upload_rejects_dangerous_html(self):
        upload = SimpleUploadedFile(
            "template.html",
            b"<html><script>alert(1)</script></html>",
            content_type="text/html",
        )
        form = CertificateTemplateAdminForm(
            data={"name": "Bad template", "description": ""},
            files={"file": upload},
        )
        self.assertFalse(form.is_valid())
        self.assertIn("file", form.errors)
