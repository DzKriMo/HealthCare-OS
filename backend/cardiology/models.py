"""Cardiology models — ECG, Echo, BP history, CV risk."""
import uuid
from django.db import models
from django.utils import timezone
from tenancy.models import Tenant
from tenancy.managers import TenantScopedManager
from patients.models import Patient


class ECGRecord(models.Model):
    """ECG recording with findings."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="ecg_records")
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="ecg_records")

    performed_date = models.DateField(default=timezone.localdate)
    heart_rate = models.IntegerField(null=True, blank=True)
    rhythm = models.CharField(max_length=100, blank=True, help_text="Sinus, AFib, etc.")
    pr_interval = models.IntegerField(null=True, blank=True, help_text="ms")
    qrs_duration = models.IntegerField(null=True, blank=True, help_text="ms")
    qt_interval = models.IntegerField(null=True, blank=True, help_text="ms")
    findings = models.TextField(blank=True)
    interpretation = models.TextField(blank=True)
    is_abnormal = models.BooleanField(default=False)

    file_path = models.CharField(max_length=1000, blank=True, help_text="ECG waveform file.")
    performed_by = models.ForeignKey("identity.User", on_delete=models.PROTECT, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = TenantScopedManager()

    class Meta:
        db_table = "cardio_ecg"
        ordering = ["-performed_date"]
        indexes = [models.Index(fields=["patient"]), models.Index(fields=["is_abnormal"])]

    def __str__(self): return f"ECG {self.performed_date} — {self.patient.full_name}"


class EchoReport(models.Model):
    """Echocardiogram report."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="echo_reports")
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="echo_reports")

    study_date = models.DateField(default=timezone.localdate)
    lvef = models.IntegerField(null=True, blank=True, help_text="LV ejection fraction %.")
    lv_ed_diameter = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    la_diameter = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    rv_function = models.CharField(max_length=50, blank=True)
    valve_findings = models.TextField(blank=True)
    findings = models.TextField(blank=True)
    conclusion = models.TextField(blank=True)

    performed_by = models.ForeignKey("identity.User", on_delete=models.PROTECT, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = TenantScopedManager()

    class Meta:
        db_table = "cardio_echo"
        ordering = ["-study_date"]

    def __str__(self): return f"Echo {self.study_date} — {self.patient.full_name}"


class BPReading(models.Model):
    """Single blood pressure reading for trend tracking."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="bp_readings")
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="bp_readings")

    systolic = models.IntegerField()
    diastolic = models.IntegerField()
    pulse = models.IntegerField(null=True, blank=True)
    recorded_at = models.DateTimeField(default=timezone.now)
    notes = models.TextField(blank=True)

    objects = TenantScopedManager()

    class Meta:
        db_table = "cardio_bp"
        ordering = ["-recorded_at"]
        indexes = [models.Index(fields=["patient"]), models.Index(fields=["recorded_at"])]

    def __str__(self): return f"BP {self.systolic}/{self.diastolic} — {self.patient.full_name}"


class CVRiskScore(models.Model):
    """Cardiovascular risk assessment."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="cv_risk_scores")
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="cv_risk_scores")

    score_type = models.CharField(max_length=30, choices=[("framingham","Framingham"),("ascvd","ASCVD")], default="ascvd")
    risk_percentage = models.DecimalField(max_digits=5, decimal_places=1, help_text="10-year risk %.")
    risk_category = models.CharField(max_length=20, choices=[("low","Low"),("moderate","Moderate"),("high","High")])
    calculated_date = models.DateField(default=timezone.localdate)
    factors = models.JSONField(default=dict, help_text="Age, sex, total cholesterol, HDL, systolic BP, treated, smoker, diabetes.")
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = TenantScopedManager()

    class Meta:
        db_table = "cardio_risk"
        ordering = ["-calculated_date"]

    def __str__(self): return f"CV Risk {self.risk_percentage}% ({self.risk_category}) — {self.patient.full_name}"
