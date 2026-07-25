"""
Tenant model with branding, settings, and module enablement.

Each tenant is an isolated organization (clinic, hospital, lab, etc.).
All core entities are scoped to a tenant.
"""
import uuid
from django.db import models
from django.core.validators import MinLengthValidator, RegexValidator


class Tenant(models.Model):
    """
    Top-level tenant/organization.

    Isolation boundaries:
        - Users, roles, patients, appointments — all tenant-scoped.
        - Branding resolved at runtime by frontend.
        - Enabled modules determine available features.
        - Settings customize behavior per tenant.

    Hierarchy support (future): parent_tenant for groups/chains.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    slug = models.SlugField(
        max_length=100,
        unique=True,
        validators=[
            MinLengthValidator(2),
            RegexValidator(
                regex=r"^[a-z0-9-]+$",
                message="Slug must be lowercase letters, numbers, and hyphens only.",
            ),
        ],
        help_text="Unique URL-safe identifier, e.g. 'smile-dental-clinic'.",
    )
    name = models.CharField(
        max_length=200,
        help_text="Display name, e.g. 'Smile Dental Clinic'.",
    )

    # Branding — JSON field for flexibility
    # Structure: { logo_url, primary_color, secondary_color, dark_mode,
    #              typography, clinic_name, language, currency }
    branding = models.JSONField(
        default=dict,
        blank=True,
        help_text="White-label branding tokens.",
    )

    # Settings — JSON field
    # Structure: { notification_channels, reminder_hours, grace_period_days,
    #              timezone, date_format, prescription_footer, invoice_footer }
    settings = models.JSONField(
        default=dict,
        blank=True,
        help_text="Per-tenant configuration.",
    )

    # Enabled modules — ordered list of module names
    # e.g. ["dental", "billing", "documents"]
    enabled_modules = models.JSONField(
        default=list,
        blank=True,
        help_text="List of enabled module names.",
    )

    # Custom domain (white-label)
    custom_domain = models.CharField(
        max_length=255,
        blank=True,
        help_text="Custom domain for white-label, e.g. 'app.smileclinic.com'.",
    )

    # Status
    is_active = models.BooleanField(
        default=True,
        help_text="Inactive tenants cannot be accessed.",
    )

    # Billing / subscription
    subscription_plan = models.CharField(max_length=100, blank=True)
    subscription_status = models.CharField(
        max_length=50,
        default="active",
        choices=[
            ("active", "Active"),
            ("trial", "Trial"),
            ("past_due", "Past Due"),
            ("cancelled", "Cancelled"),
        ],
    )
    trial_ends_at = models.DateTimeField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tenancy_tenant"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["custom_domain"]),
        ]

    def __str__(self):
        return self.name

    @property
    def is_module_enabled(self, module_name: str) -> bool:
        """Check if a module is enabled for this tenant."""
        return module_name in (self.enabled_modules or [])

    def get_branding(self) -> dict:
        """Return branding with defaults merged in."""
        defaults = {
            "logo_url": None,
            "primary_color": "#0369a1",
            "secondary_color": "#f8fafc",
            "dark_mode": False,
            "typography": "default",
            "clinic_name": self.name,
            "language": "en",
            "currency": "USD",
        }
        defaults.update(self.branding or {})
        return defaults


class TenantSettings(models.Model):
    """
    Per-tenant configuration singleton.

    Separated from the Tenant model to keep settings organized
    and allow future settings versioning/history.
    """

    tenant = models.OneToOneField(
        Tenant,
        on_delete=models.CASCADE,
        related_name="tenant_settings",
    )

    # Notification preferences
    email_enabled = models.BooleanField(default=True)
    sms_enabled = models.BooleanField(default=False)
    whatsapp_enabled = models.BooleanField(default=False)
    push_enabled = models.BooleanField(default=False)

    # Appointment defaults
    appointment_reminder_hours = models.JSONField(
        default=list,  # e.g. [24, 2]
        help_text="Hours before appointment to send reminders.",
    )
    default_appointment_duration_minutes = models.IntegerField(default=30)
    allow_online_booking = models.BooleanField(default=True)
    booking_advance_days = models.IntegerField(
        default=30,
        help_text="How many days in advance patients can book.",
    )

    # Billing defaults
    billing_grace_period_days = models.IntegerField(default=30)
    default_currency = models.CharField(max_length=3, default="USD")
    tax_rate_default = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.00,
    )
    invoice_prefix = models.CharField(max_length=10, default="INV-")
    invoice_footer = models.TextField(blank=True)
    prescription_footer = models.TextField(blank=True)

    # Localization
    timezone = models.CharField(max_length=50, default="UTC")
    date_format = models.CharField(
        max_length=20,
        default="MM/DD/YYYY",
        choices=[
            ("DD/MM/YYYY", "DD/MM/YYYY"),
            ("MM/DD/YYYY", "MM/DD/YYYY"),
            ("YYYY-MM-DD", "YYYY-MM-DD"),
        ],
    )
    language = models.CharField(max_length=10, default="en")

    # Security
    mfa_required_for_roles = models.JSONField(
        default=list,
        blank=True,
        help_text="List of role names that require MFA.",
    )
    session_timeout_minutes = models.IntegerField(default=240)
    max_failed_login_attempts = models.IntegerField(default=5)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tenancy_settings"
        verbose_name = "tenant settings"
        verbose_name_plural = "tenant settings"

    def __str__(self):
        return f"Settings for {self.tenant.name}"


# Product Editions — Sprint B17

class ProductEdition(models.Model):
    """Feature flags per edition tier."""

    class Tier(models.TextChoices):
        SOLO = "solo", "Solo Clinic"
        SPECIALIST = "specialist", "Specialist Pro"
        DIAGNOSTIC = "diagnostic", "Diagnostic Center"
        POLYCLINIC = "polyclinic", "Polyclinic"
        HOSPITAL = "hospital", "Hospital Network"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, choices=Tier.choices, unique=True)
    max_users = models.IntegerField(default=5)
    max_patients = models.IntegerField(default=0, help_text="0 = unlimited.")
    max_branches = models.IntegerField(default=1)
    enabled_modules = models.JSONField(default=list, help_text="Default modules for this edition.")
    features = models.JSONField(default=dict, help_text="Feature flags: {telehealth: true, ai_assistant: false, fhir_api: false, white_label: false}")
    monthly_price = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)

    class Meta: db_table = "tenancy_edition"

    def __str__(self): return self.get_name_display()


class CompliancePolicy(models.Model):
    """Per-tenant compliance and regulatory policy configuration."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.OneToOneField(Tenant, on_delete=models.CASCADE, related_name="compliance_policy")

    # Record retention (days)
    clinical_record_retention_days = models.IntegerField(default=3650, help_text="10 years default.")
    billing_record_retention_days = models.IntegerField(default=2555, help_text="7 years default.")
    audit_log_retention_days = models.IntegerField(default=2555)

    # Signature requirements
    require_signature_on_prescriptions = models.BooleanField(default=True)
    require_signature_on_encounters = models.BooleanField(default=True)
    require_signature_on_consents = models.BooleanField(default=True)

    # Consent rules
    consent_required_for_treatment = models.BooleanField(default=True)
    consent_required_for_data_sharing = models.BooleanField(default=True)
    consent_required_for_telehealth = models.BooleanField(default=True)
    consent_expiry_days = models.IntegerField(default=365, help_text="Consents expire after this many days.")

    # Prescription restrictions
    max_refills_per_prescription = models.IntegerField(default=12)
    prescription_expiry_days = models.IntegerField(default=365)
    require_pdmp_check = models.BooleanField(default=False, help_text="Check PDMP before prescribing controlled substances.")

    # Data export
    allow_patient_data_export = models.BooleanField(default=True)
    export_format = models.CharField(max_length=20, choices=[("fhir","FHIR"),("csv","CSV"),("pdf","PDF")], default="fhir")

    created_at = models.DateTimeField(auto_now_add=True); updated_at = models.DateTimeField(auto_now=True)

    class Meta: db_table = "tenancy_compliance"; verbose_name_plural = "compliance policies"

    def __str__(self): return f"Compliance Policy — {self.tenant.name}"


class OnboardingStep(models.Model):
    """Track onboarding progress for a tenant."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="onboarding_steps")
    step_name = models.CharField(max_length=100)
    display_order = models.IntegerField(default=1)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    completed_by = models.ForeignKey("identity.User", on_delete=models.PROTECT, null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta: db_table = "tenancy_onboarding"; ordering = ["display_order"]; unique_together = ["tenant","step_name"]

    def __str__(self): return f"{self.step_name} — {self.tenant.name} ({'done' if self.is_completed else 'pending'})"


# Default onboarding steps
DEFAULT_ONBOARDING_STEPS = [
    ("clinic_info", 1, "Enter clinic name and details"),
    ("branding", 2, "Upload logo and choose brand colors"),
    ("modules", 3, "Select and enable specialty modules"),
    ("roles", 4, "Create staff roles and assign permissions"),
    ("staff", 5, "Invite doctors, nurses, and staff"),
    ("notifications", 6, "Configure SMS/email notification settings"),
    ("billing", 7, "Set up billing items, tax rates, and payment methods"),
    ("go_live", 8, "Review settings and go live"),
]
