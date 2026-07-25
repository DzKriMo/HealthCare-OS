"""Dermatology models — Sprint B6. Body map, lesion tracking, photo timeline."""
import uuid
from django.db import models
from django.utils import timezone
from tenancy.models import Tenant
from tenancy.managers import TenantScopedManager
from patients.models import Patient


class BodyMap(models.Model):
    """A patient's body map — one per patient, tracks lesions by body region."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="body_maps")
    patient = models.OneToOneField(Patient, on_delete=models.CASCADE, related_name="body_map")
    notes = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = TenantScopedManager()

    class Meta:
        db_table = "derm_body_map"

    def __str__(self): return f"Body Map — {self.patient.full_name}"


class Lesion(models.Model):
    """A tracked skin lesion."""

    class BodyRegion(models.TextChoices):
        HEAD = "head", "Head & Neck"
        TRUNK_FRONT = "trunk_front", "Trunk (Anterior)"
        TRUNK_BACK = "trunk_back", "Trunk (Posterior)"
        ARM_LEFT = "arm_left", "Left Arm"
        ARM_RIGHT = "arm_right", "Right Arm"
        HAND_LEFT = "hand_left", "Left Hand"
        HAND_RIGHT = "hand_right", "Right Hand"
        LEG_LEFT = "leg_left", "Left Leg"
        LEG_RIGHT = "leg_right", "Right Leg"
        FOOT_LEFT = "foot_left", "Left Foot"
        FOOT_RIGHT = "foot_right", "Right Foot"
        OTHER = "other", "Other"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    body_map = models.ForeignKey(BodyMap, on_delete=models.CASCADE, related_name="lesions")
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="lesions")

    name = models.CharField(max_length=200, blank=True, help_text="Label for this lesion.")
    body_region = models.CharField(max_length=20, choices=BodyRegion.choices, default=BodyRegion.OTHER)
    location_detail = models.CharField(max_length=300, blank=True, help_text="Specific anatomical location.")

    size_mm = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    color = models.CharField(max_length=100, blank=True)
    morphology = models.CharField(max_length=200, blank=True, help_text="Macule, papule, nodule, plaque, etc.")
    border = models.CharField(max_length=100, blank=True)
    dermoscopy_findings = models.TextField(blank=True)
    clinical_impression = models.TextField(blank=True, help_text="Likely diagnosis.")
    is_biopsied = models.BooleanField(default=False)
    biopsy_result = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    discovered_date = models.DateField(default=timezone.localdate)
    recorded_by = models.ForeignKey("identity.User", on_delete=models.PROTECT, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = TenantScopedManager()

    class Meta:
        db_table = "derm_lesion"
        ordering = ["body_region", "-created_at"]
        indexes = [models.Index(fields=["patient"]), models.Index(fields=["body_region"])]

    def __str__(self): return f"Lesion: {self.name or self.location_detail} ({self.body_region})"


class LesionPhoto(models.Model):
    """Dated photo of a lesion for progression tracking."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lesion = models.ForeignKey(Lesion, on_delete=models.CASCADE, related_name="photos")
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)

    image_path = models.CharField(max_length=1000, help_text="Object storage path.")
    taken_date = models.DateField(default=timezone.localdate)
    notes = models.TextField(blank=True)
    dermoscopy = models.BooleanField(default=False, help_text="Taken with dermoscope.")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    objects = TenantScopedManager()

    class Meta:
        db_table = "derm_lesion_photo"
        ordering = ["-taken_date"]

    def __str__(self): return f"Photo {self.taken_date} — {self.lesion}"


class DermatologyProcedure(models.Model):
    """A dermatological procedure — excision, cryotherapy, biopsy, etc."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="derm_procedures")
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="derm_procedures")
    lesion = models.ForeignKey(Lesion, on_delete=models.SET_NULL, null=True, blank=True, related_name="procedures")

    procedure_type = models.CharField(max_length=50, choices=[
        ("excision","Excision"),("biopsy","Biopsy"),("cryotherapy","Cryotherapy"),
        ("curettage","Curettage"),("laser","Laser"),("other","Other")])
    description = models.TextField(blank=True)
    performed_date = models.DateField(default=timezone.localdate)
    performed_by = models.ForeignKey("identity.User", on_delete=models.PROTECT, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = TenantScopedManager()

    class Meta:
        db_table = "derm_procedure"
        ordering = ["-performed_date"]

    def __str__(self): return f"{self.procedure_type} — {self.patient.full_name}"
