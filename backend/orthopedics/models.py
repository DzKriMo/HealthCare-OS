"""Orthopedics models — Joint assessments, fractures, physiotherapy."""
import uuid
from django.db import models
from django.utils import timezone
from tenancy.models import Tenant
from tenancy.managers import TenantScopedManager
from patients.models import Patient


class JointAssessment(models.Model):
    """Range of motion and stability assessment for a joint."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="joint_assessments")
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="joint_assessments")

    joint = models.CharField(max_length=50, choices=[
        ("shoulder","Shoulder"),("elbow","Elbow"),("wrist","Wrist"),("hip","Hip"),
        ("knee","Knee"),("ankle","Ankle"),("spine","Spine"),("other","Other")])
    side = models.CharField(max_length=10, choices=[("left","Left"),("right","Right"),("bilateral","Bilateral")])
    assessment_date = models.DateField(default=timezone.localdate)
    range_of_motion = models.CharField(max_length=100, blank=True, help_text="Degrees or description.")
    strength_grade = models.IntegerField(null=True, blank=True, help_text="0-5 MRC scale.")
    stability = models.CharField(max_length=100, blank=True)
    pain_level = models.IntegerField(null=True, blank=True, help_text="0-10.")
    special_tests = models.TextField(blank=True)
    findings = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    performed_by = models.ForeignKey("identity.User", on_delete=models.PROTECT, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = TenantScopedManager()

    class Meta:
        db_table = "ortho_joint"
        ordering = ["-assessment_date"]

    def __str__(self): return f"{self.joint} ({self.side}) — {self.patient.full_name}"


class FractureRecord(models.Model):
    """Fracture diagnosis and treatment tracking."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="fracture_records")
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="fracture_records")

    bone = models.CharField(max_length=200)
    fracture_type = models.CharField(max_length=100, help_text="Simple, compound, comminuted, greenstick, etc.")
    classification = models.CharField(max_length=100, blank=True)
    side = models.CharField(max_length=10, choices=[("left","Left"),("right","Right")])
    diagnosis_date = models.DateField(default=timezone.localdate)
    treatment = models.TextField(blank=True, help_text="Cast, splint, surgery, etc.")
    healing_status = models.CharField(max_length=50, choices=[
        ("acute","Acute"),("healing","Healing"),("healed","Healed"),("non_union","Non-Union"),("malunion","Malunion")], default="acute")
    follow_up_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    diagnosed_by = models.ForeignKey("identity.User", on_delete=models.PROTECT, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = TenantScopedManager()

    class Meta:
        db_table = "ortho_fracture"
        ordering = ["-diagnosis_date"]

    def __str__(self): return f"Fracture {self.bone} ({self.side}) — {self.patient.full_name}"


class PhysiotherapyPlan(models.Model):
    """Exercise-based physiotherapy plan."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="physio_plans")
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="physio_plans")

    name = models.CharField(max_length=300)
    condition = models.CharField(max_length=300, blank=True)
    exercises = models.JSONField(default=list, help_text='[{"name":"","sets":3,"reps":10,"frequency":"daily","notes":""}]')
    start_date = models.DateField(default=timezone.localdate)
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey("identity.User", on_delete=models.PROTECT, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = TenantScopedManager()

    class Meta:
        db_table = "ortho_physio"
        ordering = ["-start_date"]

    def __str__(self): return f"Physio Plan: {self.name} — {self.patient.full_name}"
