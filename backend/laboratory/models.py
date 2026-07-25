"""
Laboratory models — Sprint B3.

TestCatalog → LabOrder → Specimen → LabResult with approval workflow.
"""
import uuid
import decimal
from django.db import models
from django.utils import timezone
from tenancy.models import Tenant
from tenancy.managers import TenantScopedManager
from patients.models import Patient


class TestCatalog(models.Model):
    """A billable lab test with reference ranges and turnaround expectations."""

    class Department(models.TextChoices):
        HEMATOLOGY = "hematology", "Hematology"
        CHEMISTRY = "chemistry", "Clinical Chemistry"
        MICROBIOLOGY = "microbiology", "Microbiology"
        IMMUNOLOGY = "immunology", "Immunology"
        PATHOLOGY = "pathology", "Pathology"
        URINALYSIS = "urinalysis", "Urinalysis"
        OTHER = "other", "Other"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="lab_tests")
    name = models.CharField(max_length=300)
    short_name = models.CharField(max_length=50, blank=True)
    department = models.CharField(max_length=20, choices=Department.choices, default=Department.CHEMISTRY)
    specimen_type = models.CharField(max_length=100, help_text="Blood, urine, swab, etc.")
    unit = models.CharField(max_length=50, blank=True, help_text="mg/dL, mm/hr, etc.")
    reference_range_low = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    reference_range_high = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    reference_range_text = models.CharField(max_length=200, blank=True, help_text="For non-numeric ranges.")
    turnaround_minutes = models.IntegerField(default=60, help_text="Expected turnaround time.")
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = TenantScopedManager()

    class Meta:
        db_table = "lab_test_catalog"
        ordering = ["department", "name"]
        constraints = [models.UniqueConstraint(fields=["tenant", "name"], name="unique_lab_test_per_tenant")]

    def __str__(self):
        return f"{self.name} ({self.department})"


class LabOrder(models.Model):
    """A doctor's order for one or more lab tests, linked to an encounter."""

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        ORDERED = "ordered", "Ordered"
        COLLECTED = "collected", "Specimen Collected"
        PROCESSING = "processing", "Processing"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="lab_orders")
    patient = models.ForeignKey(Patient, on_delete=models.PROTECT, related_name="lab_orders")
    encounter = models.ForeignKey("scheduling.Appointment", on_delete=models.SET_NULL, null=True, blank=True)
    tests = models.ManyToManyField(TestCatalog, related_name="orders")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ORDERED)
    priority = models.CharField(max_length=10, choices=[("routine","Routine"),("urgent","Urgent"),("stat","STAT")], default="routine")
    ordered_by = models.ForeignKey("identity.User", on_delete=models.PROTECT, null=True, related_name="lab_orders")
    notes = models.TextField(blank=True)
    ordered_at = models.DateTimeField(auto_now_add=True)

    objects = TenantScopedManager()

    class Meta:
        db_table = "lab_order"
        ordering = ["-ordered_at"]
        indexes = [models.Index(fields=["tenant"]), models.Index(fields=["patient"]), models.Index(fields=["status"])]

    def __str__(self):
        return f"Lab Order {self.id} — {self.patient.full_name}"


class Specimen(models.Model):
    """Physical specimen collected for a lab order."""

    class Status(models.TextChoices):
        COLLECTED = "collected", "Collected"
        RECEIVED = "received", "Received at Lab"
        PROCESSING = "processing", "Processing"
        COMPLETED = "completed", "Completed"
        REJECTED = "rejected", "Rejected"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="specimens")
    lab_order = models.ForeignKey(LabOrder, on_delete=models.CASCADE, related_name="specimens")
    barcode = models.CharField(max_length=100, unique=True, db_index=True)
    specimen_type = models.CharField(max_length=100)
    collection_date = models.DateTimeField(default=timezone.now)
    collected_by = models.ForeignKey("identity.User", on_delete=models.PROTECT, null=True, related_name="collected_specimens")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.COLLECTED)
    rejection_reason = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = TenantScopedManager()

    class Meta:
        db_table = "lab_specimen"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["barcode"]), models.Index(fields=["tenant"])]

    def __str__(self):
        return f"Specimen {self.barcode} — {self.status}"

    def transition_to(self, status: str):
        self.status = status
        self.save(update_fields=["status"])
        # Update lab order status
        order = self.lab_order
        specimens = order.specimens.all()
        if all(s.status == "completed" for s in specimens):
            order.status = LabOrder.Status.COMPLETED
        elif any(s.status == "processing" for s in specimens):
            order.status = LabOrder.Status.PROCESSING
        elif all(s.status in ("collected", "received") for s in specimens):
            order.status = LabOrder.Status.COLLECTED
        order.save(update_fields=["status"])


class LabResult(models.Model):
    """A single test result within a lab order."""

    class Flag(models.TextChoices):
        NORMAL = "normal", "Normal"
        LOW = "low", "Below Range"
        HIGH = "high", "Above Range"
        CRITICAL_LOW = "critical_low", "Critical Low"
        CRITICAL_HIGH = "critical_high", "Critical High"
        ABNORMAL = "abnormal", "Abnormal"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        REVIEWED = "reviewed", "Reviewed"
        APPROVED = "approved", "Approved"
        AMENDED = "amended", "Amended"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="lab_results")
    lab_order = models.ForeignKey(LabOrder, on_delete=models.CASCADE, related_name="results")
    test = models.ForeignKey(TestCatalog, on_delete=models.PROTECT, related_name="results")
    specimen = models.ForeignKey(Specimen, on_delete=models.CASCADE, null=True, blank=True, related_name="results")

    value = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True)
    value_text = models.CharField(max_length=500, blank=True, help_text="For qualitative results.")
    flag = models.CharField(max_length=20, choices=Flag.choices, default=Flag.NORMAL)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.DRAFT)
    is_critical = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    performed_by = models.ForeignKey("identity.User", on_delete=models.PROTECT, null=True, related_name="lab_results")
    reviewed_by = models.ForeignKey("identity.User", on_delete=models.PROTECT, null=True, blank=True, related_name="reviewed_results")
    approved_by = models.ForeignKey("identity.User", on_delete=models.PROTECT, null=True, blank=True, related_name="approved_results")

    performed_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)

    objects = TenantScopedManager()

    class Meta:
        db_table = "lab_result"
        ordering = ["-performed_at"]
        indexes = [models.Index(fields=["tenant"]), models.Index(fields=["lab_order"]), models.Index(fields=["flag"])]

    def __str__(self):
        return f"{self.test.name}: {self.value or self.value_text} ({self.flag})"

    def auto_flag(self):
        """Auto-flag based on reference ranges."""
        if self.value is None:
            return
        ref_low = self.test.reference_range_low
        ref_high = self.test.reference_range_high
        if ref_low is not None and ref_high is not None:
            if self.value < ref_low * decimal.Decimal("0.5"):
                self.flag = self.Flag.CRITICAL_LOW; self.is_critical = True
            elif self.value < ref_low:
                self.flag = self.Flag.LOW
            elif self.value > ref_high * decimal.Decimal("2"):
                self.flag = self.Flag.CRITICAL_HIGH; self.is_critical = True
            elif self.value > ref_high:
                self.flag = self.Flag.HIGH
            else:
                self.flag = self.Flag.NORMAL

    def save(self, *args, **kwargs):
        if self.value and not self.value_text:
            self.auto_flag()
        super().save(*args, **kwargs)
