"""Pruebas de autenticación y compatibilidad con hashes heredados."""

from __future__ import annotations

import bcrypt
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from .hashers import PHPBCryptPasswordHasher
from .models import User


class LegacyHasherTests(TestCase):
    def test_php_bcrypt_hash_is_verified(self):
        hasher = PHPBCryptPasswordHasher()
        encoded = hasher.encode("LegacyPassword123!", "")
        self.assertTrue(encoded.startswith("php_bcrypt$"))
        self.assertTrue(hasher.verify("LegacyPassword123!", encoded))
        self.assertFalse(hasher.verify("WrongPassword", encoded))

    def test_php_2y_prefix_is_accepted(self):
        raw = bcrypt.hashpw(b"LegacyPassword123!", bcrypt.gensalt()).decode("ascii")
        # PHP genera hashes con prefijo $2y$; bcrypt de Python usa $2b$.
        raw = "$2y$" + raw[4:]
        hasher = PHPBCryptPasswordHasher()
        encoded = f"php_bcrypt${raw}"
        self.assertTrue(hasher.verify("LegacyPassword123!", encoded))

    def test_login_upgrades_legacy_hash_to_argon2(self):
        raw = bcrypt.hashpw(b"LegacyPassword123!", bcrypt.gensalt()).decode("ascii")
        user = User.objects.create(
            email="legacy@example.test",
            full_name="Legacy User",
            password=f"php_bcrypt${raw}",
            role=User.Role.SUPERADMIN,
            is_staff=True,
        )
        cache.clear()
        response = self.client.post(
            reverse("admin:login"),
            {"username": user.email, "password": "LegacyPassword123!"},
        )
        self.assertEqual(response.status_code, 302)
        user.refresh_from_db()
        self.assertTrue(user.password.startswith("argon2$"))

    def test_invalid_login_is_rejected(self):
        User.objects.create_user(
            email="user@example.test",
            password="ValidPassword123!",
            full_name="User",
        )
        cache.clear()
        response = self.client.post(
            reverse("admin:login"),
            {"username": "user@example.test", "password": "wrong"},
            HTTP_ACCEPT_LANGUAGE="en",
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid email or password")
