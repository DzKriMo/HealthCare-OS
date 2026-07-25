"""
Document and file models — Sprint 5.

Core entities:
    Document — file reference with tenant-scoped storage, categories, versioning.
    Signature — captured signature (SVG) with metadata.
"""
import uuid
from django.db import models
from tenancy.models import Tenant
from tenancy.managers import TenantScopedManager
from patients.models import Patient


class Document(models.Model):
    """
    File/document reference with tenant-scoped object storage.

    Binary data is stored in MinIO/S3 at paths like:
        {tenant_slug}/patients/{patient_uuid}/documents/{category}/{file_id}.ext

    Signed URLs provide time-limited access without exposing storage internals.
    """

    class Category(models.TextChoices):
        CONSENT = "consent", "Consent Form"
        LAB = "lab", "Lab Result"
        REFERRAL = "referral", "Referral Letter"
        IMAGING = "imaging", "Medical Image"
        PRESCRIPTION = "prescription", "Prescription"
        INVOICE = "invoice", "Invoice"
        REPORT = "report", "Report"
        INSURANCE = "insurance", "Insurance Card"
        IDENTITY = "identity", "ID Document"
        OTHER = "other", "Other"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="documents")
    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name="documents", null=True, blank=True,
    )

    # File metadata
    file_name = models.CharField(max_length=500)
    file_size = models.BigIntegerField(help_text="Size in bytes.")
    mime_type = models.CharField(max_length=100)
    storage_path = models.CharField(
        max_length=1000, help_text="Object storage key/path.",
    )
    file_hash = models.CharField(
        max_length=64, blank=True, help_text="SHA-256 hash for integrity verification.",
    )

    # Classification
    category = models.CharField(max_length=30, choices=Category.choices, default=Category.OTHER)
    tags = models.JSONField(default=list, help_text="User-defined tags for filtering.")
    description = models.TextField(blank=True)

    # Versioning
    version = models.PositiveIntegerField(default=1)
    replaces = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="replaced_by",
        help_text="Previous version this document replaces.",
    )

    # Status
    is_archived = models.BooleanField(default=False)
    is_sensitive = models.BooleanField(
        default=False, help_text="Flag for extra access logging.",
    )

    # Dimensions (images)
    width = models.IntegerField(null=True, blank=True)
    height = models.IntegerField(null=True, blank=True)

    # Audit
    uploaded_by = models.ForeignKey(
        "identity.User", on_delete=models.PROTECT, null=True, related_name="uploaded_documents",
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = TenantScopedManager()

    class Meta:
        db_table = "documents_document"
        ordering = ["-uploaded_at"]
        indexes = [
            models.Index(fields=["tenant"]),
            models.Index(fields=["tenant", "patient"]),
            models.Index(fields=["tenant", "category"]),
            models.Index(fields=["storage_path"]),
        ]

    def __str__(self):
        return f"{self.file_name} ({self.category})"

    @property
    def size_display(self) -> str:
        """Human-readable file size."""
        if self.file_size < 1024:
            return f"{self.file_size} B"
        elif self.file_size < 1024 * 1024:
            return f"{self.file_size / 1024:.1f} KB"
        return f"{self.file_size / (1024 * 1024):.1f} MB"

    def get_storage_prefix(self) -> str:
        """Generate tenant-scoped storage prefix."""
        patient_segment = f"patients/{self.patient_id}" if self.patient_id else "general"
        return f"{self.tenant.slug}/{patient_segment}/{self.category.lower()}"


class Signature(models.Model):
    """
    Captured signature — stored as SVG with audit metadata.

    Linked to encounters, consents, invoices, or any signable record.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="signatures")
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="signatures")

    # SVG content of the signature
    svg_data = models.TextField(help_text="Raw SVG path data of the signature.")

    # What this signature applies to
    entity_type = models.CharField(max_length=50, help_text="e.g., encounter, consent, invoice.")
    entity_id = models.UUIDField()

    # Metadata
    signed_by_name = models.CharField(max_length=200, help_text="Name of the signer.")
    signed_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    objects = TenantScopedManager()

    class Meta:
        db_table = "documents_signature"
        ordering = ["-signed_at"]
        indexes = [
            models.Index(fields=["tenant"]),
            models.Index(fields=["entity_type", "entity_id"]),
        ]

    def __str__(self):
        return f"Signature by {self.signed_by_name} on {self.entity_type}/{self.entity_id}"
