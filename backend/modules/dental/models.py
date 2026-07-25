"""
Dental module models — odontogram, tooth charting, procedures, treatment plans.
"""
import uuid
from django.db import models
from tenancy.models import Tenant
from tenancy.managers import TenantScopedManager
from patients.models import Patient


class ToothChart(models.Model):
    """
    A patient's odontogram — the full dental chart.

    One chart per patient. Tracks the state of each tooth (FDI notation, 1-48).
    Permanent teeth: 11-18 (UR), 21-28 (UL), 31-38 (LR), 41-48 (LL).
    Primary teeth: 51-55, 61-65, 71-75, 81-85.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="tooth_charts")
    patient = models.OneToOneField(Patient, on_delete=models.CASCADE, related_name="tooth_chart")
    notes = models.TextField(blank=True)
    last_updated_by = models.ForeignKey(
        "identity.User", on_delete=models.PROTECT, null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = TenantScopedManager()

    class Meta:
        db_table = "dental_tooth_chart"

    def __str__(self):
        return f"Chart: {self.patient.full_name}"


class Tooth(models.Model):
    """
    A single tooth on the odontogram.

    Identified by FDI number. Tracks condition, notes, and treatment history.
    """

    class Condition(models.TextChoices):
        HEALTHY = "healthy", "Healthy"
        FILLED = "filled", "Filled"
        DECAYED = "decayed", "Decayed"
        CROWNED = "crowned", "Crowned"
        MISSING = "missing", "Missing"
        IMPLANT = "implant", "Implant"
        BRIDGE = "bridge", "Bridge Abutment"
        ROOT_CANAL = "root_canal", "Root Canal Treated"
        VENEER = "veneer", "Veneer"
        FRACTURED = "fractured", "Fractured"
        ABSCESS = "abscess", "Abscess"
        OTHER = "other", "Other"

    class Quadrant(models.TextChoices):
        UR = "ur", "Upper Right"
        UL = "ul", "Upper Left"
        LR = "lr", "Lower Right"
        LL = "ll", "Lower Left"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chart = models.ForeignKey(ToothChart, on_delete=models.CASCADE, related_name="teeth")
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)

    fdi_number = models.IntegerField(help_text="FDI tooth number (11-48 permanent, 51-85 primary).")
    condition = models.CharField(max_length=20, choices=Condition.choices, default=Condition.HEALTHY)
    notes = models.TextField(blank=True)
    surface_data = models.JSONField(
        default=dict, blank=True,
        help_text="Per-surface conditions: {'mesial': 'decayed', 'occlusal': 'filled', ...}",
    )

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "dental_tooth"
        ordering = ["fdi_number"]
        unique_together = ["chart", "fdi_number"]
        indexes = [
            models.Index(fields=["chart"]),
            models.Index(fields=["tenant"]),
        ]

    def __str__(self):
        return f"Tooth #{self.fdi_number} ({self.condition}) — {self.chart.patient.full_name}"

    @property
    def quadrant(self) -> str:
        tens = self.fdi_number // 10
        quad_map = {1: "ur", 2: "ul", 3: "lr", 4: "ll", 5: "ur", 6: "ul", 7: "lr", 8: "ll"}
        return quad_map.get(tens, "unknown")

    @property
    def is_primary(self) -> bool:
        return 50 <= self.fdi_number <= 85

    @property
    def is_permanent(self) -> bool:
        return 11 <= self.fdi_number <= 48


class ToothProcedure(models.Model):
    """
    A dental procedure performed on a specific tooth.

    Tracks: filling, extraction, root canal, crown prep, implant placement, etc.
    """

    class ProcedureType(models.TextChoices):
        FILLING_COMPOSITE = "filling_composite", "Composite Filling"
        FILLING_AMALGAM = "filling_amalgam", "Amalgam Filling"
        EXTRACTION = "extraction", "Extraction"
        ROOT_CANAL = "root_canal", "Root Canal Treatment"
        CROWN_PREP = "crown_prep", "Crown Preparation"
        CROWN_CEMENT = "crown_cement", "Crown Cementation"
        IMPLANT_PLACEMENT = "implant_placement", "Implant Placement"
        VENEER = "veneer", "Veneer"
        BRIDGE = "bridge", "Bridge"
        SCALING = "scaling", "Scaling & Root Planing"
        WHITENING = "whitening", "Whitening"
        EXAM = "exam", "Examination"
        XRAY = "xray", "X-Ray"
        OTHER = "other", "Other"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tooth = models.ForeignKey(Tooth, on_delete=models.CASCADE, related_name="procedures")
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="dental_procedures")
    appointment = models.ForeignKey(
        "scheduling.Appointment", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="dental_procedures",
    )

    procedure_type = models.CharField(max_length=30, choices=ProcedureType.choices)
    surfaces = models.JSONField(
        default=list, blank=True,
        help_text="Surfaces treated: ['mesial', 'occlusal', 'distal', 'buccal', 'lingual']",
    )
    description = models.TextField(blank=True)
    performed_by = models.ForeignKey(
        "identity.User", on_delete=models.PROTECT, null=True, related_name="dental_procedures",
    )
    performed_at = models.DateTimeField(auto_now_add=True)

    # Materials used
    materials = models.JSONField(default=list, blank=True, help_text="Materials used in the procedure.")

    objects = TenantScopedManager()

    class Meta:
        db_table = "dental_procedure"
        ordering = ["-performed_at"]
        indexes = [
            models.Index(fields=["tooth"]),
            models.Index(fields=["patient"]),
            models.Index(fields=["tenant"]),
        ]

    def __str__(self):
        return f"{self.get_procedure_type_display()} on #{self.tooth.fdi_number} — {self.patient.full_name}"


class Implant(models.Model):
    """Dental implant tracking — brand, size, placement date, follow-up schedule."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tooth = models.OneToOneField(Tooth, on_delete=models.CASCADE, related_name="implant")
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="implants")

    brand = models.CharField(max_length=200, blank=True)
    model_name = models.CharField(max_length=200, blank=True)
    diameter_mm = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    length_mm = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    placement_date = models.DateField()
    restoration_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    objects = TenantScopedManager()

    class Meta:
        db_table = "dental_implant"
        indexes = [models.Index(fields=["patient"])]

    def __str__(self):
        return f"Implant #{self.tooth.fdi_number} — {self.patient.full_name}"


class Crown(models.Model):
    """Crown tracking — material, cementation date, lab information."""

    class Material(models.TextChoices):
        PFM = "pfm", "Porcelain-Fused-to-Metal"
        ZIRCONIA = "zirconia", "Zirconia"
        EMAX = "emax", "E-Max (Lithium Disilicate)"
        FULL_METAL = "full_metal", "Full Metal"
        GOLD = "gold", "Gold"
        OTHER = "other", "Other"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tooth = models.OneToOneField(Tooth, on_delete=models.CASCADE, related_name="crown")
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="crowns")

    material = models.CharField(max_length=20, choices=Material.choices, default=Material.ZIRCONIA)
    prep_date = models.DateField()
    cementation_date = models.DateField(null=True, blank=True)
    lab_name = models.CharField(max_length=200, blank=True)
    lab_tracking = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    objects = TenantScopedManager()

    class Meta:
        db_table = "dental_crown"
        indexes = [models.Index(fields=["patient"])]

    def __str__(self):
        return f"Crown #{self.tooth.fdi_number} ({self.material}) — {self.patient.full_name}"


class DentalTreatmentPlan(models.Model):
    """
    Multi-phase dental treatment plan.

    Each phase contains multiple planned procedures. Tracks estimated costs,
    insurance coverage, consent status, and completion progress.
    """

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PRESENTED = "presented", "Presented to Patient"
        ACCEPTED = "accepted", "Accepted"
        IN_PROGRESS = "in_progress", "In Progress"
        COMPLETED = "completed", "Completed"
        DECLINED = "declined", "Declined"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="dental_plans")
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="dental_plans")
    created_by = models.ForeignKey(
        "identity.User", on_delete=models.PROTECT, null=True, related_name="dental_plans",
    )

    name = models.CharField(max_length=300)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    notes = models.TextField(blank=True)

    estimated_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    insurance_estimate = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    patient_portion = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    consent_signed = models.BooleanField(default=False)
    consent_signed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = TenantScopedManager()

    class Meta:
        db_table = "dental_treatment_plan"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["tenant"]),
            models.Index(fields=["patient"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"Plan: {self.name} — {self.patient.full_name}"


class TreatmentPlanPhase(models.Model):
    """A phase within a treatment plan, containing planned procedures."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    plan = models.ForeignKey(DentalTreatmentPlan, on_delete=models.CASCADE, related_name="phases")
    name = models.CharField(max_length=200)
    order = models.PositiveIntegerField(default=1)
    description = models.TextField(blank=True)
    is_completed = models.BooleanField(default=False)

    estimated_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "dental_treatment_phase"
        ordering = ["plan", "order"]

    def __str__(self):
        return f"Phase {self.order}: {self.name}"


class PlannedProcedure(models.Model):
    """A planned procedure within a treatment plan phase."""

    class Priority(models.TextChoices):
        URGENT = "urgent", "Urgent"
        HIGH = "high", "High"
        NORMAL = "normal", "Normal"
        LOW = "low", "Low"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phase = models.ForeignKey(TreatmentPlanPhase, on_delete=models.CASCADE, related_name="procedures")
    tooth = models.ForeignKey(Tooth, on_delete=models.CASCADE, related_name="planned_procedures", null=True, blank=True)

    procedure_type = models.CharField(max_length=30, choices=ToothProcedure.ProcedureType.choices)
    description = models.TextField(blank=True)
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.NORMAL)
    estimated_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_completed = models.BooleanField(default=False)
    completed_procedure = models.ForeignKey(
        ToothProcedure, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="fulfilled_plan",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "dental_planned_procedure"
        ordering = ["phase", "priority", "created_at"]

    def __str__(self):
        return f"{self.get_procedure_type_display()} — Phase: {self.phase.name}"
