"""Hasher compatible con los hashes bcrypt generados por PHP.

Los hashes heredados se guardan con el prefijo ``php_bcrypt$`` para que Django
sepa qué algoritmo usar. Tras el primer inicio de sesión se re-hashea la
contraseña con Argon2 (primer hasher configurado).
"""

from __future__ import annotations

import bcrypt
from django.contrib.auth.hashers import BasePasswordHasher
from django.utils.crypto import constant_time_compare


class PHPBCryptPasswordHasher(BasePasswordHasher):
    algorithm = "php_bcrypt"

    def salt(self) -> str:
        return ""

    def encode(self, password: str, salt: str) -> str:
        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("ascii")
        return f"{self.algorithm}${hashed}"

    def verify(self, password: str, encoded: str) -> bool:
        if not encoded.startswith(f"{self.algorithm}$"):
            return False
        raw = encoded.split("$", 1)[1]
        # PHP usa $2y$; la librería bcrypt de Python acepta $2b$/$2a$.
        if raw.startswith("$2y$"):
            raw = "$2b$" + raw[4:]
        try:
            return bcrypt.checkpw(password.encode("utf-8"), raw.encode("ascii"))
        except (ValueError, TypeError):
            return False

    def decode(self, encoded: str) -> dict[str, str]:
        return {"algorithm": self.algorithm, "hash": encoded}

    def must_update(self, encoded: str) -> bool:
        # Forzamos la actualización a Argon2 en el siguiente inicio de sesión.
        return True

    def harden_runtime(self, password: str, encoded: str) -> None:
        # bcrypt ya aplica un coste adecuado; no se requiere trabajo adicional.
        return None
