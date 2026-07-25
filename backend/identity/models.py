"""
Identity models: Custom User, Role, Permission, Session tracking.

Core of Sprint 1 — every other domain depends on knowing who the user is,
which tenant they belong to, and what they're allowed to do.
"""
import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from django.core.validators import MinLengthValidator


# ── User Manager ──────────────────────────────────────────────

class UserManager(BaseUserManager):
    """Custom manager that uses email as the unique identifier."""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        extra_fields.setdefault("is_active", True)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self.create_user(email, password, **extra_fields)


# ── Permission ────────────────────────────────────────────────

class Permission(models.Model):
    """
    Fine-grained permission following resource.action convention.

    Examples:
        - patients.read
        - patients.write_demographics
        - billing.refund
        - inventory.adjust_stock
        - modules.dental.access
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codename = models.CharField(
        max_length=120,
        unique=True,
        validators=[MinLengthValidator(3)],
        help_text="Resource.action format, e.g. 'patients.read'",
    )
    description = models.CharField(max_length=300)
    resource = models.CharField(
        max_length=60,
        help_text="Resource category: patients, billing, records, etc.",
    )
    action = models.CharField(
        max_length=60,
        help_text="Action: read, write, write_demographics, refund, etc.",
    )

    class Meta:
        db_table = "identity_permission"
        ordering = ["resource", "action"]
        indexes = [
            models.Index(fields=["resource"]),
            models.Index(fields=["codename"]),
        ]

    def __str__(self):
        return self.codename


# ── Role ──────────────────────────────────────────────────────

class Role(models.Model):
    """
    Tenant-scoped role with M2M permissions.

    System roles (is_system_role=True) have no tenant and are available
    as templates across all tenants. Tenant roles are created by tenant
    admins for custom permission groupings.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        "tenancy.Tenant",
        on_delete=models.CASCADE,
        related_name="roles",
        null=True,
        blank=True,
        help_text="Null for system roles (templates across tenants).",
    )
    name = models.CharField(max_length=100)
    is_system_role = models.BooleanField(
        default=False,
        help_text="System roles are templates available to all tenants.",
    )
    permissions = models.ManyToManyField(
        Permission,
        related_name="roles",
        blank=True,
    )
    description = models.TextField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "identity_role"
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "name"],
                name="unique_role_name_per_tenant",
            ),
        ]
        indexes = [
            models.Index(fields=["tenant"]),
        ]

    def __str__(self):
        tenant_slug = self.tenant.slug if self.tenant else "system"
        return f"{self.name} ({tenant_slug})"


# ── User ──────────────────────────────────────────────────────

class User(AbstractBaseUser):
    """
    Custom user model.

    Key design decisions:
        - UUID primary key (sync-safe, no sequential ID leakage).
        - Email as the login identifier (USERNAME_FIELD).
        - Tenant FK is nullable for super admins (cross-tenant access).
        - MFA fields stored encrypted at rest.
        - Practitioner profile embedded for clinical users.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        "tenancy.Tenant",
        on_delete=models.PROTECT,
        related_name="users",
        null=True,
        blank=True,
        help_text="Null for platform super admins.",
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.PROTECT,
        related_name="users",
        null=True,
        blank=True,
        help_text="Primary role determining base permissions.",
    )

    # Identity
    email = models.EmailField(unique=True, db_index=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)

    # Status
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(
        default=False,
        help_text="Access to Django admin.",
    )
    is_superuser = models.BooleanField(
        default=False,
        help_text="Cross-tenant platform access.",
    )

    # MFA
    mfa_enabled = models.BooleanField(default=False)
    mfa_secret = models.CharField(
        max_length=255,
        blank=True,
        help_text="Encrypted TOTP secret.",
    )

    # Practitioner profile (nullable — not all users are clinicians)
    license_number = models.CharField(max_length=100, blank=True)
    specialty = models.CharField(max_length=100, blank=True)
    department = models.CharField(max_length=100, blank=True)

    # Password reset tracking
    password_changed_at = models.DateTimeField(null=True, blank=True)
    password_reset_required = models.BooleanField(default=False)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    class Meta:
        db_table = "identity_user"
        verbose_name = "user"
        verbose_name_plural = "users"
        ordering = ["last_name", "first_name"]
        indexes = [
            models.Index(fields=["tenant"]),
            models.Index(fields=["tenant", "role"]),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @property
    def is_practitioner(self) -> bool:
        return bool(self.license_number)

    @property
    def effective_permissions(self) -> set[str]:
        """Return the set of permission codenames from the user's role."""
        if not self.role:
            return set()
        return set(
            self.role.permissions.values_list("codename", flat=True)
        )

    # Django admin compatibility (normally from PermissionsMixin)
    def has_perm(self, perm, obj=None):
        return self.is_superuser or self.is_staff

    def has_module_perms(self, app_label):
        return self.is_superuser or self.is_staff

    def has_permission(self, codename: str) -> bool:
        """Check if the user has a specific permission via their role."""
        if not self.is_active:
            return False
        # Super admins bypass permission checks
        if self.is_superuser:
            return True
        return codename in self.effective_permissions


# ── User Session ──────────────────────────────────────────────

class UserSession(models.Model):
    """
    Track active user sessions for security management.

    Each session corresponds to a JWT refresh token. Users can
    view and revoke their own sessions. Admins can revoke any
    session for their tenant.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="sessions",
    )
    tenant = models.ForeignKey(
        "tenancy.Tenant",
        on_delete=models.CASCADE,
        related_name="sessions",
        null=True,
        blank=True,
        help_text="Null for super admin sessions.",
    )
    refresh_token_jti = models.CharField(
        max_length=255,
        unique=True,
        help_text="JWT ID of the refresh token.",
    )
    device_name = models.CharField(max_length=200, blank=True)
    device_type = models.CharField(
        max_length=50,
        blank=True,
        help_text="web, desktop, mobile",
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    location = models.CharField(
        max_length=200,
        blank=True,
        help_text="Approximate geo-location (city, country).",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "identity_session"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["refresh_token_jti"]),
        ]

    @property
    def is_active(self) -> bool:
        if self.revoked_at:
            return False
        return self.expires_at > timezone.now()

    def revoke(self):
        """Revoke this session."""
        self.revoked_at = timezone.now()
        self.save(update_fields=["revoked_at"])


# ── Device (for trusted device tracking) ──────────────────────

class Device(models.Model):
    """
    Trusted device tracking for risk-based authentication.

    Devices that have successfully passed 2FA can be marked as
    trusted for a configurable period, reducing MFA prompts.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="devices",
    )
    device_fingerprint = models.CharField(max_length=255)
    device_name = models.CharField(max_length=200, blank=True)
    is_trusted = models.BooleanField(default=False)
    trusted_until = models.DateTimeField(null=True, blank=True)

    first_seen_at = models.DateTimeField(auto_now_add=True)
    last_seen_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "identity_device"
        unique_together = ["user", "device_fingerprint"]
        indexes = [
            models.Index(fields=["user", "device_fingerprint"]),
        ]
