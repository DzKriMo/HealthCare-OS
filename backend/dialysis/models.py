"""Dialysis models."""
import uuid; from django.db import models; from django.utils import timezone
from tenancy.models import Tenant; from tenancy.managers import TenantScopedManager; from patients.models import Patient

class DialysisSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="dialysis_sessions")
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="dialysis_sessions")
    session_date = models.DateField(default=timezone.localdate)
    dialysis_type = models.CharField(max_length=20, choices=[("hemodialysis","Hemodialysis"),("peritoneal","Peritoneal")], default="hemodialysis")
    duration_minutes = models.IntegerField(null=True, blank=True)
    pre_weight_kg = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    post_weight_kg = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    fluid_removed_ml = models.IntegerField(null=True, blank=True)
    pre_bp_systolic = models.IntegerField(null=True, blank=True); pre_bp_diastolic = models.IntegerField(null=True, blank=True)
    post_bp_systolic = models.IntegerField(null=True, blank=True); post_bp_diastolic = models.IntegerField(null=True, blank=True)
    access_site = models.CharField(max_length=200, blank=True, help_text="AV fistula, graft, catheter site.")
    access_site_condition = models.CharField(max_length=100, blank=True)
    complications = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    practitioner = models.ForeignKey("identity.User", on_delete=models.PROTECT, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    objects = TenantScopedManager()
    class Meta:
        db_table = "dialysis_session"; ordering = ["-session_date"]
        indexes = [models.Index(fields=["patient"]), models.Index(fields=["session_date"])]
    def __str__(self): return f"Dialysis {self.session_date} — {self.patient.full_name}"

    @property
    def weight_loss_kg(self):
        if self.pre_weight_kg and self.post_weight_kg:
            return float(self.pre_weight_kg) - float(self.post_weight_kg)
        return None
