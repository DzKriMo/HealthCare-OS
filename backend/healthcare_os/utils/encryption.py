"""
Application-level field encryption for PHI (P3.8, P8.2).

Uses Fernet (AES-128-CBC + HMAC). The key is derived from
``settings.FIELD_ENCRYPTION_KEY`` (a urlsafe base64 32-byte key). In dev it
falls back to a key derived from SECRET_KEY so tests run without extra config.
"""
import base64
import hashlib
from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.db import models


@lru_cache(maxsize=1)
def _fernet() -> Fernet:
    key = getattr(settings, "FIELD_ENCRYPTION_KEY", "") or ""
    if not key:
        # Derive a stable key from SECRET_KEY (dev/test only).
        digest = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
        key = base64.urlsafe_b64encode(digest).decode()
    if isinstance(key, str):
        key = key.encode()
    return Fernet(key)


def encrypt_value(plaintext: str) -> str:
    if plaintext in (None, ""):
        return ""
    return _fernet().encrypt(plaintext.encode()).decode()


def decrypt_value(ciphertext: str) -> str:
    if ciphertext in (None, ""):
        return ""
    try:
        return _fernet().decrypt(ciphertext.encode()).decode()
    except (InvalidToken, ValueError):
        # Legacy plaintext value (pre-encryption) — return as-is.
        return ciphertext


class EncryptedCharField(models.CharField):
    """A CharField that transparently encrypts its value at rest."""

    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        if value in (None, ""):
            return value
        return encrypt_value(value)

    def from_db_value(self, value, expression, connection):
        if value in (None, ""):
            return value
        return decrypt_value(value)
