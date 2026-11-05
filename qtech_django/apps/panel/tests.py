"""Pruebas del panel operativo."""

from __future__ import annotations

import unittest
from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User
from apps.certificates.models import Certificate, CertificateEvent
from apps.certificates.pdf import pdf_backend_available

PASSWORD = "Str0ng-Passw0rd-2026"


class PanelBaseTestCase(TestCase):
    def setUp(self):
        self.superadmin = User.objects.create_superuser(
            email="owner@example.com",
            password=PASSWORD,
            full_name="Owner User",
        )
        self.analyst = User.objects.create_user(
            email="analyst@example.com",
            password=PASSWORD,
            full_name="Analyst User",
        )
        self.certificate = Certificate.objects.create(
            code="PANEL-001",
            applicant="Example Client",
            product="Testing device",
            issue_date=timezone.localdate(),
            expiry_date=timezone.localdate() + timedelta(days=365),
        )


class PanelAccessTests(PanelBaseTestCase):
    def test_anonymous_is_redirected_to_panel_login(self):
        response = self.client.get(reverse("panel:dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("panel:login"), response["Location"])

    def test_analyst_can_use_certificates(self):
        self.client.force_login(self.analyst)
        for name in ("panel:dashboard", "panel:certificate_list", "panel:activity"):
            self.assertEqual(self.client.get(reverse(name)).status_code, 200)

    def test_analyst_cannot_manage_users(self):
        self.client.force_login(self.analyst)
        response = self.client.get(reverse("panel:user_list"))
        self.assertEqual(response.status_code, 403)

    def test_login_page_is_available(self):
        response = self.client.get(reverse("panel:login"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "QTech")

    def test_login_redirects_to_panel_dashboard(self):
        response = self.client.post(
            reverse("panel:login"),
            {"username": "owner@example.com", "password": PASSWORD},
        )
        self.assertRedirects(response, reverse("panel:dashboard"))


class PanelCertificateTests(PanelBaseTestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.analyst)

    def test_list_filters_by_status_and_query(self):
        response = self.client.get(
            reverse("panel:certificate_list"), {"q": "PANEL", "status": "valid"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "PANEL-001")

    def test_detail_shows_certificate_and_downloads(self):
        response = self.client.get(
            reverse("panel:certificate_detail", args=[self.certificate.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "PANEL-001")
        self.assertContains(response, "PDF")

    def test_create_certificate(self):
        response = self.client.post(
            reverse("panel:certificate_create"),
            {
                "code": "PANEL-002",
                "applicant": "New Client",
                "product": "New product",
                "issue_date": timezone.localdate().isoformat(),
                "expiry_date": (timezone.localdate() + timedelta(days=365)).isoformat(),
                "status": Certificate.Status.ACTIVE,
                "show_parameters": "on",
            },
        )
        certificate = Certificate.objects.get(code="PANEL-002")
        self.assertRedirects(
            response, reverse("panel:certificate_detail", args=[certificate.pk])
        )
        self.assertEqual(certificate.analyst, self.analyst)
        self.assertTrue(
            certificate.events.filter(event=CertificateEvent.Event.CREATED).exists()
        )

    def test_edit_certificate(self):
        response = self.client.post(
            reverse("panel:certificate_edit", args=[self.certificate.pk]),
            {
                "code": "PANEL-001",
                "applicant": "Updated Client",
                "product": "Testing device",
                "issue_date": self.certificate.issue_date.isoformat(),
                "expiry_date": self.certificate.expiry_date.isoformat(),
                "status": Certificate.Status.ACTIVE,
                "show_parameters": "on",
            },
        )
        self.assertRedirects(
            response,
            reverse("panel:certificate_detail", args=[self.certificate.pk]),
        )
        self.certificate.refresh_from_db()
        self.assertEqual(self.certificate.applicant, "Updated Client")

    def test_status_toggle_and_token_regeneration(self):
        response = self.client.post(
            reverse("panel:certificate_status", args=[self.certificate.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.certificate.refresh_from_db()
        self.assertEqual(self.certificate.status, Certificate.Status.BLOCKED)

        old_token = self.certificate.token
        response = self.client.post(
            reverse("panel:certificate_regenerate_token", args=[self.certificate.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.certificate.refresh_from_db()
        self.assertNotEqual(self.certificate.token, old_token)

    def test_html_and_qr_downloads(self):
        html_response = self.client.get(
            reverse(
                "panel:certificate_html",
                args=[self.certificate.pk, "en"],
            )
            + "?download=1"
        )
        self.assertEqual(html_response.status_code, 200)
        self.assertIn("attachment", html_response["Content-Disposition"])

        qr_response = self.client.get(
            reverse("panel:certificate_qr", args=[self.certificate.pk])
        )
        self.assertEqual(qr_response.status_code, 200)
        self.assertEqual(qr_response["Content-Type"], "image/png")

    @unittest.skipUnless(pdf_backend_available(), "No hay motor de PDF instalado")
    def test_pdf_download(self):
        response = self.client.get(
            reverse("panel:certificate_pdf", args=[self.certificate.pk, "en"])
            + "?download=1"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn("attachment", response["Content-Disposition"])


class PanelUserTests(PanelBaseTestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.superadmin)

    def test_user_list(self):
        response = self.client.get(reverse("panel:user_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "owner@example.com")

    def test_create_user(self):
        response = self.client.post(
            reverse("panel:user_create"),
            {
                "email": "new@example.com",
                "full_name": "New User",
                "role": User.Role.ANALYST,
                "is_active": "on",
                "password1": PASSWORD,
                "password2": PASSWORD,
            },
        )
        self.assertRedirects(response, reverse("panel:user_list"))
        user = User.objects.get(email="new@example.com")
        self.assertTrue(user.is_staff)
        self.assertTrue(user.check_password(PASSWORD))

    def test_edit_user(self):
        response = self.client.post(
            reverse("panel:user_edit", args=[self.analyst.pk]),
            {
                "email": "analyst@example.com",
                "full_name": "Analyst Updated",
                "role": User.Role.ANALYST,
                "is_active": "on",
            },
        )
        self.assertRedirects(response, reverse("panel:user_list"))
        self.analyst.refresh_from_db()
        self.assertEqual(self.analyst.full_name, "Analyst Updated")

    def test_change_user_password(self):
        response = self.client.post(
            reverse("panel:user_password", args=[self.analyst.pk]),
            {
                "new_password1": "N3w-Passw0rd-2026",
                "new_password2": "N3w-Passw0rd-2026",
            },
        )
        self.assertRedirects(response, reverse("panel:user_list"))
        self.analyst.refresh_from_db()
        self.assertTrue(self.analyst.check_password("N3w-Passw0rd-2026"))

    def test_superadmin_cannot_demote_self(self):
        response = self.client.post(
            reverse("panel:user_edit", args=[self.superadmin.pk]),
            {
                "email": "owner@example.com",
                "full_name": "Owner User",
                "role": User.Role.ANALYST,
                "is_active": "on",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.superadmin.refresh_from_db()
        self.assertEqual(self.superadmin.role, User.Role.SUPERADMIN)
