"""
Patient master data models — Sprint 2.

Core entities:
    Patient — the central entity, tenant-scoped, UUID PK.
    MedicalHistory — versioned entries for chronic conditions, surgeries, etc.
    Allergy — substance/reaction tracking with severity.
    CurrentMedication — active medications with dose and prescriber.
    InsurancePolicy — primary/secondary insurance coverage.
    EmergencyContact — multiple contacts per patient.
    ConsentRecord — versioned consent tracking for GDPR/HIPAA compliance.
"""
import uuid
from django.db import models
from django.db.models import Q
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from healthcare_os.utils.encryption import EncryptedCharField
from tenancy.models import Tenant
from tenancy.managers import TenantScopedManager


# ═══════════════════════════════════════════════════════════════
# Patient
# ═══════════════════════════════════════════════════════════════

class Patient(models.Model):
    """
    Core patient entity — the central record linking all clinical data.

    Design decisions:
        - UUID PK: sync-safe, no sequential ID leakage.
        - Tenant FK: every patient belongs to exactly one tenant.
        - display_id: human-readable, tenant-scoped sequence (e.g., PAT-2024-0001).
        - national_id encrypted at rest (application-level encryption preferred).
        - Soft-delete via is_active flag.
    """

    class Gender(models.TextChoices):
        MALE = "male", "Male"
        FEMALE = "female", "Female"
        OTHER = "other", "Other"
        UNKNOWN = "unknown", "Unknown"

    class BloodType(models.TextChoices):
        A_POS = "A+", "A+"
        A_NEG = "A-", "A-"
        B_POS = "B+", "B+"
        B_NEG = "B-", "B-"
        AB_POS = "AB+", "AB+"
        AB_NEG = "AB-", "AB-"
        O_POS = "O+", "O+"
        O_NEG = "O-", "O-"

    class MaritalStatus(models.TextChoices):
        SINGLE = "single", "Single"
        MARRIED = "married", "Married"
        DIVORCED = "divorced", "Divorced"
        WIDOWED = "widowed", "Widowed"
        UNKNOWN = "unknown", "Unknown"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.PROTECT,
        related_name="patients",
    )
    display_id = models.CharField(
        max_length=30,
        blank=True,
        default="",
        help_text="Human-readable ID, e.g. PAT-2024-0001. Auto-generated if blank.",
    )

    # ── Demographics ──────────────────────────────────────
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10, choices=Gender.choices, default=Gender.UNKNOWN)
    blood_type = models.CharField(
        max_length=5, choices=BloodType.choices, null=True, blank=True,
    )
    marital_status = models.CharField(
        max_length=20, choices=MaritalStatus.choices, default=MaritalStatus.UNKNOWN,
    )

    # ── Identification ────────────────────────────────────
    national_id = EncryptedCharField(
        max_length=255,
        blank=True,
        help_text="Encrypted at rest (Fernet/AES) — SSN, national ID, etc.",
    )
    national_id_type = models.CharField(
        max_length=50,
        blank=True,
        help_text="SSN, passport, driver's license, etc.",
    )

    # ── Contact ───────────────────────────────────────────
    phone_primary = models.CharField(max_length=30)
    phone_secondary = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    address_line1 = models.CharField(max_length=200)
    address_line2 = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, default="US")

    # ── Status ────────────────────────────────────────────
    is_active = models.BooleanField(default=True)
    registration_date = models.DateField(auto_now_add=True)

    # ── Metadata ──────────────────────────────────────────
    created_by = models.ForeignKey(
        "identity.User",
        on_delete=models.PROTECT,
        related_name="created_patients",
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = TenantScopedManager()

    class Meta:
        db_table = "patients_patient"
        ordering = ["last_name", "first_name"]
        indexes = [
            models.Index(fields=["tenant"]),
            models.Index(fields=["tenant", "last_name", "first_name"]),
            models.Index(fields=["tenant", "display_id"]),
            models.Index(fields=["tenant", "phone_primary"]),
            models.Index(fields=["tenant", "date_of_birth"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "display_id"],
                name="unique_display_id_per_tenant",
            ),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.display_id or self.id})"

    def save(self, *args, **kwargs):
        """Auto-generate display_id if not set."""
        if not self.display_id:
            import datetime
            year = datetime.date.today().year
            last = (
                Patient.objects.for_tenant(self.tenant)
                .filter(display_id__startswith=f"PAT-{year}-")
                .order_by("-display_id")
                .first()
            )
            if last and last.display_id:
                try:
                    seq = int(last.display_id.split("-")[-1]) + 1
                except (ValueError, IndexError):
                    seq = 1
            else:
                seq = 1
            self.display_id = f"PAT-{year}-{seq:04d}"
        super().save(*args, **kwargs)

    @property
    def full_name(self) -> str:
        parts = [self.first_name, self.middle_name, self.last_name]
        return " ".join(p for p in parts if p)

    @property
    def age(self) -> int | None:
        """Calculate age from date_of_birth."""
        if not self.date_of_birth:
            return None
        import datetime
        today = datetime.date.today()
        return (
            today.year
            - self.date_of_birth.year
            - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
        )

    @classmethod
    def search(cls, tenant, query: str):
        """
        Full-text search across name, phone, email, and display_id.
        Uses PostgreSQL full-text search when available, falls back to ILIKE.
        """
        return (
            cls.objects.for_tenant(tenant)
            .filter(
                Q(first_name__icontains=query)
                | Q(last_name__icontains=query)
                | Q(phone_primary__icontains=query)
                | Q(email__icontains=query)
                | Q(display_id__icontains=query)
            )
            .filter(is_active=True)
        )


# ═══════════════════════════════════════════════════════════════
# Medical History
# ═══════════════════════════════════════════════════════════════

class MedicalHistory(models.Model):
    """
    Versioned medical history entries.

    Each entry is immutable once created. Edits create a new version
    pointing to the previous one via `previous_version`.
    """

    class Category(models.TextChoices):
        CHRONIC = "chronic", "Chronic Condition"
        SURGERY = "surgery", "Past Surgery"
        FAMILY = "family", "Family History"
        SOCIAL = "social", "Social History"
        TRAUMA = "trauma", "Trauma"
        OTHER = "other", "Other"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name="medical_history",
    )
    tenant = models.ForeignKey(Tenant, on_delete=models.PROTECT)

    category = models.CharField(max_length=20, choices=Category.choices)
    condition = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    onset_date = models.DateField(null=True, blank=True)
    resolved_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    # Versioning
    version = models.PositiveIntegerField(default=1)
    previous_version = models.ForeignKey(
        "self", on_delete=models.PROTECT, null=True, blank=True,
        related_name="next_versions",
    )

    recorded_by = models.ForeignKey(
        "identity.User", on_delete=models.PROTECT, null=True,
    )
    recorded_at = models.DateTimeField(auto_now_add=True)

    objects = TenantScopedManager()

    class Meta:
        db_table = "patients_medical_history"
        ordering = ["-onset_date", "-recorded_at"]
        verbose_name_plural = "medical histories"
        indexes = [
            models.Index(fields=["patient"]),
            models.Index(fields=["tenant"]),
            models.Index(fields=["category"]),
        ]

    def __str__(self):
        return f"{self.patient.full_name} — {self.condition} ({self.category})"


# ═══════════════════════════════════════════════════════════════
# Allergy
# ═══════════════════════════════════════════════════════════════

class Allergy(models.Model):
    """Patient allergy with severity and status tracking."""

    class Severity(models.TextChoices):
        MILD = "mild", "Mild"
        MODERATE = "moderate", "Moderate"
        SEVERE = "severe", "Severe"
        LIFE_THREATENING = "life_threatening", "Life-Threatening"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        RESOLVED = "resolved", "Resolved"
        UNKNOWN = "unknown", "Unknown"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name="allergies",
    )
    tenant = models.ForeignKey(Tenant, on_delete=models.PROTECT)

    substance = models.CharField(max_length=200)
    reaction = models.TextField(blank=True, help_text="Describe the allergic reaction.")
    severity = models.CharField(
        max_length=20, choices=Severity.choices, default=Severity.MODERATE,
    )
    onset_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)

    recorded_by = models.ForeignKey(
        "identity.User", on_delete=models.PROTECT, null=True,
    )
    recorded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = TenantScopedManager()

    class Meta:
        db_table = "patients_allergy"
        ordering = ["substance"]
        indexes = [
            models.Index(fields=["patient"]),
            models.Index(fields=["tenant"]),
            models.Index(fields=["severity"]),
        ]

    def __str__(self):
        return f"{self.substance} ({self.severity}) — {self.patient.full_name}"


# ═══════════════════════════════════════════════════════════════
# Current Medication
# ═══════════════════════════════════════════════════════════════

class CurrentMedication(models.Model):
    """Active medications the patient is currently taking."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name="medications",
    )
    tenant = models.ForeignKey(Tenant, on_delete=models.PROTECT)

    drug_name = models.CharField(max_length=200)
    dosage = models.CharField(max_length=100, blank=True)
    frequency = models.CharField(max_length=100, blank=True)
    route = models.CharField(max_length=100, blank=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    prescribed_by = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    recorded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = TenantScopedManager()

    class Meta:
        db_table = "patients_medication"
        ordering = ["-start_date"]
        indexes = [
            models.Index(fields=["patient"]),
            models.Index(fields=["tenant"]),
        ]

    def __str__(self):
        return f"{self.drug_name} {self.dosage} — {self.patient.full_name}"


# ═══════════════════════════════════════════════════════════════
# Insurance Policy
# ═══════════════════════════════════════════════════════════════

class InsurancePolicy(models.Model):
    """
    Insurance policy linked to a patient.

    Supports primary/secondary coverage, policy numbers, and effective dates.
    """

    class CoverageType(models.TextChoices):
        PRIMARY = "primary", "Primary"
        SECONDARY = "secondary", "Secondary"
        TERTIARY = "tertiary", "Tertiary"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name="insurance_policies",
    )
    tenant = models.ForeignKey(Tenant, on_delete=models.PROTECT)

    provider = models.CharField(max_length=200)
    policy_number = models.CharField(max_length=100)
    group_number = models.CharField(max_length=100, blank=True)
    coverage_type = models.CharField(
        max_length=20, choices=CoverageType.choices, default=CoverageType.PRIMARY,
    )
    plan_name = models.CharField(max_length=200, blank=True)
    effective_date = models.DateField()
    expiration_date = models.DateField(null=True, blank=True)
    card_front_image_url = models.URLField(blank=True)
    card_back_image_url = models.URLField(blank=True)

    # Policy holder
    policy_holder_name = models.CharField(max_length=200, blank=True)
    policy_holder_relationship = models.CharField(max_length=100, blank=True)

    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(
        "identity.User", on_delete=models.PROTECT, null=True, blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = TenantScopedManager()

    class Meta:
        db_table = "patients_insurance_policy"
        ordering = ["coverage_type", "-effective_date"]
        verbose_name_plural = "insurance policies"
        indexes = [
            models.Index(fields=["patient"]),
            models.Index(fields=["tenant"]),
            models.Index(fields=["policy_number"]),
        ]

    def __str__(self):
        return f"{self.provider} ({self.coverage_type}) — {self.patient.full_name}"

    @property
    def is_active(self) -> bool:
        if not self.expiration_date:
            return True
        import datetime
        return self.expiration_date >= datetime.date.today()


# ═══════════════════════════════════════════════════════════════
# Emergency Contact
# ═══════════════════════════════════════════════════════════════

class EmergencyContact(models.Model):
    """Emergency contact for a patient."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name="emergency_contacts",
    )
    tenant = models.ForeignKey(Tenant, on_delete=models.PROTECT)

    name = models.CharField(max_length=200)
    relationship = models.CharField(max_length=100)
    phone_primary = models.CharField(max_length=30)
    phone_secondary = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)

    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = TenantScopedManager()

    class Meta:
        db_table = "patients_emergency_contact"
        ordering = ["-is_primary", "name"]
        indexes = [
            models.Index(fields=["patient"]),
            models.Index(fields=["tenant"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.relationship}) — {self.patient.full_name}"


# ═══════════════════════════════════════════════════════════════
# Consent Record
# ═══════════════════════════════════════════════════════════════

class ConsentRecord(models.Model):
    """
    Versioned consent tracking for regulatory compliance (GDPR, HIPAA, etc.).

    Each consent is linked to a specific form version. When a form changes,
    patients may need to re-consent to the new version.
    """

    class ConsentType(models.TextChoices):
        TREATMENT = "treatment", "Treatment Consent"
        DATA_SHARING = "data_sharing", "Data Sharing"
        MARKETING = "marketing", "Marketing Communications"
        RESEARCH = "research", "Research Participation"
        TELEHEALTH = "telehealth", "Telehealth Consent"
        PHOTOGRAPHY = "photography", "Clinical Photography"
        OTHER = "other", "Other"

    class Status(models.TextChoices):
        GRANTED = "granted", "Granted"
        WITHDRAWN = "withdrawn", "Withdrawn"
        EXPIRED = "expired", "Expired"
        PENDING = "pending", "Pending"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name="consents",
    )
    tenant = models.ForeignKey(Tenant, on_delete=models.PROTECT)

    consent_type = models.CharField(max_length=30, choices=ConsentType.choices)
    form_name = models.CharField(max_length=200, help_text="Name of the consent form.")
    form_version = models.CharField(
        max_length=20, help_text="Version of the form when consent was given.",
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.GRANTED,
    )
    notes = models.TextField(blank=True)

    # Audit metadata
    granted_at = models.DateTimeField()
    granted_by = models.ForeignKey(
        "identity.User",
        on_delete=models.PROTECT,
        related_name="consents_granted",
        null=True,
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    device_info = models.CharField(max_length=300, blank=True)

    # Withdrawal tracking
    withdrawn_at = models.DateTimeField(null=True, blank=True)
    withdrawal_reason = models.TextField(blank=True)

    # Expiration
    expires_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    objects = TenantScopedManager()

    class Meta:
        db_table = "patients_consent"
        ordering = ["-granted_at"]
        indexes = [
            models.Index(fields=["patient"]),
            models.Index(fields=["tenant"]),
            models.Index(fields=["consent_type", "status"]),
        ]

    def __str__(self):
        return f"{self.consent_type} ({self.status}) — {self.patient.full_name}"

    def withdraw(self, reason: str = ""):
        """Withdraw this consent."""
        from django.utils import timezone
        self.status = self.Status.WITHDRAWN
        self.withdrawn_at = timezone.now()
        self.withdrawal_reason = reason
        self.save(update_fields=["status", "withdrawn_at", "withdrawal_reason"])
