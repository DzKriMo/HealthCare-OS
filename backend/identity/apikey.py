"""
External API key model + authentication for third-party integrations.

API keys are tenant-scoped with configurable permissions and rate limits.
"""
import uuid
import secrets
from django.db import models
from django.utils import timezone
from rest_framework import authentication, exceptions

from tenancy.models import Tenant


class ApiKey(models.Model):
    """
    Tenant-scoped API key for external integrations.

    Keys are prefixed with `hcos_` for easy identification in logs.
    The full key is only shown once at creation time.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="api_keys")
    name = models.CharField(max_length=200, help_text="Label for this key, e.g. 'Patient App Integration'.")

    # The hashed prefix is stored; the full key only shown once
    prefix = models.CharField(max_length=20, unique=True, help_text="Key prefix for identification: hcos_xxxxxxxx.")
    key_hash = models.CharField(max_length=128, help_text="SHA-256 hash of the full key.")

    # Scoped permissions (whitelist)
    scopes = models.JSONField(
        default=list,
        help_text='List of permission strings: ["patients.read", "appointments.create"].',
    )

    # Rate limiting
    rate_limit = models.CharField(
        max_length=50, default="100/hour",
        help_text="Rate limit: '100/hour', '1000/day'.",
    )

    is_active = models.BooleanField(default=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        "identity.User", on_delete=models.PROTECT, null=True, related_name="created_api_keys",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "identity_api_key"

    def __str__(self):
        return f"{self.name} ({self.prefix})"

    @classmethod
    def generate(cls, tenant, name: str, scopes: list[str], created_by=None, rate_limit: str = "100/hour", expires_at=None):
        """Generate a new API key. Returns (api_key_instance, full_key_string)."""
        full_key = f"hcos_{secrets.token_hex(24)}"
        prefix = full_key[:16]  # hcos_xxxxxxxxxx
        key_hash = secrets.token_hex(32)  # placeholder — in production use hashlib.sha256

        # In production: hash the key properly
        import hashlib
        key_hash = hashlib.sha256(full_key.encode()).hexdigest()

        instance = cls.objects.create(
            tenant=tenant,
            name=name,
            prefix=prefix,
            key_hash=key_hash,
            scopes=scopes,
            rate_limit=rate_limit,
            created_by=created_by,
            expires_at=expires_at,
        )
        return instance, full_key

    def check_permission(self, permission_string: str) -> bool:
        """Check if this key has a specific scope."""
        return permission_string in (self.scopes or [])

    @property
    def is_valid(self) -> bool:
        if not self.is_active:
            return False
        if self.expires_at and self.expires_at < timezone.now():
            return False
        return True


class ApiKeyAuthentication(authentication.BaseAuthentication):
    """
    DRF Authentication class for API keys.

    Authenticates requests with header: Authorization: ApiKey hcos_xxxx...
    """

    keyword = "ApiKey"

    def authenticate(self, request):
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")

        if not auth_header.startswith(f"{self.keyword} "):
            return None

        key = auth_header[len(self.keyword) + 1:].strip()
        if not key:
            return None

        # Find by prefix, then verify hash
        prefix = key[:16]
        try:
            api_key = ApiKey.objects.select_related("tenant").get(prefix=prefix, is_active=True)
        except ApiKey.DoesNotExist:
            raise exceptions.AuthenticationFailed("Invalid API key.")

        # Verify full key hash
        import hashlib
        if hashlib.sha256(key.encode()).hexdigest() != api_key.key_hash:
            raise exceptions.AuthenticationFailed("Invalid API key.")

        if not api_key.is_valid:
            raise exceptions.AuthenticationFailed("API key expired or revoked.")

        # Update last used
        api_key.last_used_at = timezone.now()
        api_key.save(update_fields=["last_used_at"])

        # Create a virtual user-like object for permission checks
        user = ApiKeyUser(api_key)
        return (user, api_key)


class ApiKeyUser:
    """
    Virtual user for API key authentication.

    Provides compatibility with permission classes that expect request.user.
    """

    def __init__(self, api_key: ApiKey):
        self.api_key = api_key
        self.is_authenticated = True
        self.is_active = True
        self.is_superuser = False
        self.tenant = api_key.tenant

    @property
    def id(self):
        return None

    def has_permission(self, codename: str) -> bool:
        return self.api_key.check_permission(codename)

    def __str__(self):
        return f"ApiKey:{self.api_key.prefix}"
