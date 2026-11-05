"""Pruebas de la web pública y del cambio de idioma."""

from __future__ import annotations

from urllib.parse import parse_qs, urlparse

from django.test import RequestFactory, TestCase
from django.urls import reverse

from .templatetags.qtech_tags import admin_language_url, language_url


class PublicPageTests(TestCase):
    def test_home_page(self):
        response = self.client.get(reverse("core:home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Qingdao")

    def test_verify_page(self):
        response = self.client.get(reverse("certificates:verify"))
        self.assertEqual(response.status_code, 200)

    def test_health_check(self):
        response = self.client.get(reverse("health"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["database"], "ok")

    def test_robots_disallows_private_areas(self):
        response = self.client.get(reverse("robots_txt"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Disallow: /control/")
        self.assertContains(response, "Disallow: /verify/")


class LanguageTests(TestCase):
    def test_public_language_switch(self):
        response = self.client.get(
            reverse("set_language"), {"lang": "en", "next": "/verify/"}
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/verify/")
        self.assertEqual(response.cookies["django_language"].value, "en")

    def test_admin_language_is_limited_to_chinese_and_english(self):
        response = self.client.get(
            reverse("set_language"), {"lang": "es", "next": "/control/"}
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.cookies["django_language"].value, "zh-hans")

    def test_spanish_is_not_available_on_public_site(self):
        response = self.client.get(
            reverse("set_language"), {"lang": "es", "next": "/verify/"}
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.cookies["django_language"].value, "zh-hans")

    def test_public_language_menu_only_lists_chinese_and_english(self):
        response = self.client.get(reverse("core:home"))
        self.assertContains(response, "中文")
        self.assertContains(response, "English")
        self.assertNotContains(response, "Español")

    def test_external_next_url_is_rejected(self):
        response = self.client.get(
            reverse("set_language"),
            {"lang": "en", "next": "https://evil.example/phishing"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/")

    def test_language_url_encodes_the_next_parameter(self):
        request = RequestFactory().get("/verify/?q=ABC-123&lang=en")
        url = language_url(request, "zh-hans")
        parsed = parse_qs(urlparse(url).query)
        self.assertEqual(parsed["lang"], ["zh-hans"])
        self.assertEqual(parsed["next"], ["/verify/?q=ABC-123&lang=en"])

    def test_admin_language_url_never_uses_spanish(self):
        request = RequestFactory().get("/control/certificates/certificate/")
        url = admin_language_url(request, "es")
        parsed = parse_qs(urlparse(url).query)
        self.assertEqual(parsed["lang"], ["zh-hans"])
        self.assertEqual(parsed["next"], ["/control/certificates/certificate/"])
