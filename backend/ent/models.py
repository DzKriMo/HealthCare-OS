"""ENT models — Audiology exams, endoscopy records."""
import uuid
from django.db import models
from django.utils import timezone
from tenancy.models import Tenant
from tenancy.managers import TenantScopedManager
from patients.models import Patient


class AudiologyExam(models.Model):
    """Hearing test / audiogram."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="audiology_exams")
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="audiology_exams")

    exam_date = models.DateField(default=timezone.localdate)
    test_type = models.CharField(max_length=30, choices=[
        ("pure_tone","Pure Tone Audiometry"),("tympanometry","Tympanometry"),
        ("speech","Speech Audiometry"),("oae","OAE"),("abr","ABR")])

    # Right ear thresholds (dB at frequencies)
    thresholds_od = models.JSONField(default=dict, help_text='{"500Hz":15,"1000Hz":20,"2000Hz":25,"4000Hz":30}')
    thresholds_os = models.JSONField(default=dict)

    hearing_loss_type = models.CharField(max_length=30, blank=True, choices=[
        ("normal","Normal"),("conductive","Conductive"),("sensorineural","Sensorineural"),("mixed","Mixed")])
    hearing_loss_severity = models.CharField(max_length=20, blank=True, choices=[
        ("none","None"),("mild","Mild"),("moderate","Moderate"),("severe","Severe"),("profound","Profound")])
    findings = models.TextField(blank=True)
    recommendations = models.TextField(blank=True)

    performed_by = models.ForeignKey("identity.User", on_delete=models.PROTECT, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = TenantScopedManager()

    class Meta:
        db_table = "ent_audiology"
        ordering = ["-exam_date"]

    def __str__(self): return f"Audiology {self.exam_date} — {self.patient.full_name}"


class EndoscopyRecord(models.Model):
    """Nasal, laryngeal, or otoscopic endoscopy."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="endoscopy_records")
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="endoscopy_records")

    procedure_date = models.DateField(default=timezone.localdate)
    endoscopy_type = models.CharField(max_length=30, choices=[
        ("nasal","Nasal Endoscopy"),("laryngeal","Laryngoscopy"),("otoscopic","Otoscopy")])
    findings = models.TextField(blank=True)
    diagnosis = models.TextField(blank=True)
    images_paths = models.JSONField(default=list, help_text="List of image file paths.")
    notes = models.TextField(blank=True)

    performed_by = models.ForeignKey("identity.User", on_delete=models.PROTECT, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = TenantScopedManager()

    class Meta:
        db_table = "ent_endoscopy"
        ordering = ["-procedure_date"]

    def __str__(self): return f"{self.endoscopy_type} {self.procedure_date} — {self.patient.full_name}"
