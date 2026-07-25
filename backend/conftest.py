"""
Pytest configuration for Healthcare OS backend.
"""
import pytest
from django.conf import settings
from django.core.cache import cache


def pytest_configure():
    """Configure test environment."""
    settings.DEBUG = False
    settings.PASSWORD_HASHERS = [
        "django.contrib.auth.hashers.MD5PasswordHasher",
    ]


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """Enable database access for all tests by default."""
    pass


@pytest.fixture(autouse=True)
def clear_cache_between_tests():
    """Clear Redis cache between tests so rate-limit/brute-force counters don't bleed."""
    cache.clear()
    yield
    cache.clear()
