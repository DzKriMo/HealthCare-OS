"""Gynecology models — OB history, Pap smears, antenatal visits."""
import uuid
from django.db import models
from django.utils import timezone
from tenancy.models import Tenant
from tenancy.managers import TenantScopedManager
from patients.models import Patient


class OBHistory(models.Model):
    """Obstetric history for a patient."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="ob_histories")
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="ob_histories")

    gravida = models.IntegerField(default=0, help_text="Total pregnancies.")
    para = models.IntegerField(default=0, help_text="Pregnancies carried past 20 weeks.")
    abortus = models.IntegerField(default=0, help_text="Pregnancy losses before 20 weeks.")
    lmp = models.DateField(null=True, blank=True, help_text="Last menstrual period.")
    edd = models.DateField(null=True, blank=True, help_text="Estimated due date.")
    notes = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = TenantScopedManager()

    class Meta:
        db_table = "gyn_ob_history"
        verbose_name_plural = "OB histories"

    def __str__(self): return f"OB History G{self.gravida}P{self.para}A{self.abortus} — {self.patient.full_name}"


class PapSmear(models.Model):
    """Pap smear test result."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="pap_smears")
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="pap_smears")

    performed_date = models.DateField(default=timezone.localdate)
    result = models.CharField(max_length=50, choices=[
        ("normal","Normal"),("ascus","ASC-US"),("lsil","LSIL"),("hsil","HSIL"),
        ("agc","AGC"),("other","Other")])
    hpv_co_test = models.BooleanField(default=False)
    hpv_positive = models.BooleanField(null=True, blank=True)
    follow_up_recommended = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)

    performed_by = models.ForeignKey("identity.User", on_delete=models.PROTECT, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = TenantScopedManager()

    class Meta:
        db_table = "gyn_pap"
        ordering = ["-performed_date"]

    def __str__(self): return f"Pap {self.performed_date} — {self.patient.full_name} ({self.result})"


class AntenatalVisit(models.Model):
    """Pregnancy checkup visit."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="antenatal_visits")
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="antenatal_visits")

    visit_date = models.DateField(default=timezone.localdate)
    gestational_weeks = models.IntegerField()
    weight_kg = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    bp_systolic = models.IntegerField(null=True, blank=True)
    bp_diastolic = models.IntegerField(null=True, blank=True)
    fundal_height_cm = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    fetal_hr = models.IntegerField(null=True, blank=True)
    fetal_movement = models.BooleanField(null=True)
    ultrasound_findings = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    practitioner = models.ForeignKey("identity.User", on_delete=models.PROTECT, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = TenantScopedManager()

    class Meta:
        db_table = "gyn_antenatal"
        ordering = ["-visit_date"]

    def __str__(self): return f"Antenatal W{self.gestational_weeks} — {self.patient.full_name}"
