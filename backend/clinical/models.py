"""
Clinical/General Medicine models — Sprint B5.
Encounter (SOAP), Diagnosis (ICD-10), Referral, VitalSigns, Vaccination, FamilyHistory, SocialHistory.
"""
import uuid
from django.db import models
from django.utils import timezone
from tenancy.models import Tenant
from tenancy.managers import TenantScopedManager
from patients.models import Patient


class Encounter(models.Model):
    """SOAP note encounter linked to an appointment."""

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        IN_PROGRESS = "in_progress", "In Progress"
        FINALIZED = "finalized", "Finalized"
        SIGNED = "signed", "Signed"
        AMENDED = "amended", "Amended"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="encounters")
    patient = models.ForeignKey(Patient, on_delete=models.PROTECT, related_name="encounters")
    appointment = models.OneToOneField("scheduling.Appointment", on_delete=models.SET_NULL, null=True, blank=True, related_name="encounter")

    # SOAP
    subjective = models.TextField(blank=True, help_text="Chief complaint, history of present illness.")
    objective = models.TextField(blank=True, help_text="Physical exam findings, vitals summary.")
    assessment = models.TextField(blank=True, help_text="Diagnosis, differential, clinical impression.")
    plan = models.TextField(blank=True, help_text="Treatment plan, orders, follow-up.")

    status = models.CharField(max_length=15, choices=Status.choices, default=Status.DRAFT)
    encounter_date = models.DateField(default=timezone.localdate)
    duration_minutes = models.IntegerField(null=True, blank=True)

    practitioner = models.ForeignKey("identity.User", on_delete=models.PROTECT, null=True, related_name="encounters")
    signed_by = models.ForeignKey("identity.User", on_delete=models.PROTECT, null=True, blank=True, related_name="signed_encounters")
    signed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = TenantScopedManager()

    class Meta:
        db_table = "clinical_encounter"
        ordering = ["-encounter_date"]
        indexes = [models.Index(fields=["tenant"]), models.Index(fields=["patient"]), models.Index(fields=["status"])]

    def __str__(self): return f"Encounter {self.encounter_date} — {self.patient.full_name}"


class Diagnosis(models.Model):
    """ICD-10 coded diagnosis."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="diagnoses")
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="diagnoses")
    encounter = models.ForeignKey(Encounter, on_delete=models.CASCADE, null=True, blank=True, related_name="diagnoses")

    icd_code = models.CharField(max_length=10, help_text="ICD-10 code, e.g. J45.909")
    description = models.CharField(max_length=500)
    diagnosis_type = models.CharField(max_length=20, choices=[("primary","Primary"),("secondary","Secondary"),("admitting","Admitting"),("discharge","Discharge")], default="primary")
    is_chronic = models.BooleanField(default=False)
    onset_date = models.DateField(null=True, blank=True)
    resolved_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    recorded_by = models.ForeignKey("identity.User", on_delete=models.PROTECT, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = TenantScopedManager()

    class Meta:
        db_table = "clinical_diagnosis"
        ordering = ["diagnosis_type", "-created_at"]
        indexes = [models.Index(fields=["patient"]), models.Index(fields=["icd_code"])]

    def __str__(self): return f"{self.icd_code} — {self.description}"


class Referral(models.Model):
    """Referral to a specialist."""

    class Urgency(models.TextChoices):
        ROUTINE = "routine", "Routine"
        URGENT = "urgent", "Urgent"
        STAT = "stat", "STAT"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="referrals")
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="referrals")
    encounter = models.ForeignKey(Encounter, on_delete=models.SET_NULL, null=True, blank=True, related_name="referrals")

    referring_practitioner = models.ForeignKey("identity.User", on_delete=models.PROTECT, null=True, related_name="referrals_out")
    specialist_name = models.CharField(max_length=200)
    specialty = models.CharField(max_length=200)
    reason = models.TextField()
    urgency = models.CharField(max_length=10, choices=Urgency.choices, default=Urgency.ROUTINE)
    status = models.CharField(max_length=20, choices=[("pending","Pending"),("scheduled","Scheduled"),("completed","Completed"),("declined","Declined")], default="pending")
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    objects = TenantScopedManager()

    class Meta:
        db_table = "clinical_referral"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["patient"]), models.Index(fields=["status"])]

    def __str__(self): return f"Referral to {self.specialist_name} — {self.patient.full_name}"


class VitalSigns(models.Model):
    """A set of vital signs recorded at a point in time."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="vital_signs")
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="vital_signs")
    encounter = models.ForeignKey(Encounter, on_delete=models.CASCADE, null=True, blank=True, related_name="vital_signs")

    systolic_bp = models.IntegerField(null=True, blank=True)
    diastolic_bp = models.IntegerField(null=True, blank=True)
    heart_rate = models.IntegerField(null=True, blank=True)
    respiratory_rate = models.IntegerField(null=True, blank=True)
    temperature_c = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    oxygen_saturation = models.IntegerField(null=True, blank=True)
    height_cm = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    weight_kg = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    bmi = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True, help_text="Auto-calculated.")
    pain_score = models.IntegerField(null=True, blank=True, help_text="0-10 scale.")
    recorded_at = models.DateTimeField(default=timezone.now)
    recorded_by = models.ForeignKey("identity.User", on_delete=models.PROTECT, null=True)
    notes = models.TextField(blank=True)

    objects = TenantScopedManager()

    class Meta:
        db_table = "clinical_vitals"
        ordering = ["-recorded_at"]
        indexes = [models.Index(fields=["patient"]), models.Index(fields=["recorded_at"])]

    def __str__(self): return f"Vitals {self.recorded_at:%Y-%m-%d %H:%M} — {self.patient.full_name}"

    def save(self, *args, **kwargs):
        if self.weight_kg and self.height_cm and float(self.height_cm) > 0:
            h_m = float(self.height_cm) / 100
            self.bmi = round(float(self.weight_kg) / (h_m * h_m), 1)
        super().save(*args, **kwargs)


class Vaccination(models.Model):
    """Administered vaccine record."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="vaccinations")
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="vaccinations")

    vaccine_name = models.CharField(max_length=300)
    dose_number = models.IntegerField(default=1)
    lot_number = models.CharField(max_length=100, blank=True)
    administration_site = models.CharField(max_length=100, blank=True, help_text="e.g. Left deltoid")
    administered_date = models.DateField()
    next_due_date = models.DateField(null=True, blank=True)
    administered_by = models.ForeignKey("identity.User", on_delete=models.PROTECT, null=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = TenantScopedManager()

    class Meta:
        db_table = "clinical_vaccination"
        ordering = ["-administered_date"]

    def __str__(self): return f"{self.vaccine_name} dose {self.dose_number} — {self.patient.full_name}"


class FamilyHistory(models.Model):
    """Family medical history."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="family_history")
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="family_history")
    relationship = models.CharField(max_length=100, help_text="e.g. Mother, Father, Sibling")
    condition = models.CharField(max_length=300)
    age_at_onset = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=[("living","Living"),("deceased","Deceased")], blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = TenantScopedManager()

    class Meta:
        db_table = "clinical_family_history"
        ordering = ["relationship"]

    def __str__(self): return f"{self.relationship} — {self.condition}"


class SocialHistory(models.Model):
    """Social and lifestyle history."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="social_history")
    patient = models.OneToOneField(Patient, on_delete=models.CASCADE, related_name="social_history")

    smoking_status = models.CharField(max_length=30, choices=[
        ("never","Never"),("former","Former"),("current","Current"),("unknown","Unknown")], default="unknown")
    alcohol_use = models.CharField(max_length=30, choices=[
        ("none","None"),("occasional","Occasional"),("moderate","Moderate"),("heavy","Heavy"),("unknown","Unknown")], default="unknown")
    exercise_frequency = models.CharField(max_length=30, choices=[
        ("none","None"),("occasional","Occasional"),("regular","Regular"),("daily","Daily"),("unknown","Unknown")], default="unknown")
    occupation = models.CharField(max_length=200, blank=True)
    diet_description = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = TenantScopedManager()

    class Meta:
        db_table = "clinical_social_history"
        verbose_name_plural = "social histories"

    def __str__(self): return f"Social History — {self.patient.full_name}"
