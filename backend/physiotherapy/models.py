"""Physiotherapy models."""
import uuid; from django.db import models; from django.utils import timezone
from tenancy.models import Tenant; from tenancy.managers import TenantScopedManager; from patients.models import Patient

class PhysiotherapySession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="physio_sessions")
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="physio_sessions")
    session_date = models.DateField(default=timezone.localdate)
    treatment_type = models.CharField(max_length=100)
    exercises_performed = models.JSONField(default=list, help_text='[{"name":"","sets":3,"reps":10,"notes":""}]')
    subjective = models.TextField(blank=True)
    objective = models.TextField(blank=True)
    assessment = models.TextField(blank=True)
    plan = models.TextField(blank=True)
    pain_pre = models.IntegerField(null=True, blank=True, help_text="0-10 before session.")
    pain_post = models.IntegerField(null=True, blank=True, help_text="0-10 after session.")
    duration_minutes = models.IntegerField(null=True, blank=True)
    practitioner = models.ForeignKey("identity.User", on_delete=models.PROTECT, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    objects = TenantScopedManager()
    class Meta:
        db_table = "physio_session"; ordering = ["-session_date"]
        indexes = [models.Index(fields=["patient"]), models.Index(fields=["session_date"])]
    def __str__(self): return f"Physio {self.session_date} — {self.patient.full_name}"
