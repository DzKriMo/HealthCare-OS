"""Oncology models — staging, chemo, tumor markers."""
import uuid; from django.db import models; from django.utils import timezone
from tenancy.models import Tenant; from tenancy.managers import TenantScopedManager; from patients.models import Patient

class CancerStaging(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="cancer_stagings")
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="cancer_stagings")
    diagnosis = models.CharField(max_length=300, help_text="Cancer type.")
    tnm_t = models.CharField(max_length=10, blank=True); tnm_n = models.CharField(max_length=10, blank=True); tnm_m = models.CharField(max_length=10, blank=True)
    stage = models.CharField(max_length=10, choices=[("I","I"),("II","II"),("III","III"),("IV","IV")], blank=True)
    diagnosis_date = models.DateField(default=timezone.localdate)
    notes = models.TextField(blank=True)
    recorded_by = models.ForeignKey("identity.User", on_delete=models.PROTECT, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    objects = TenantScopedManager()
    class Meta: db_table = "onc_staging"; ordering = ["-diagnosis_date"]
    def __str__(self): return f"{self.diagnosis} Stage {self.stage} — {self.patient.full_name}"

class ChemotherapyProtocol(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="chemo_protocols")
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="chemo_protocols")
    protocol_name = models.CharField(max_length=300)
    drugs = models.JSONField(default=list, help_text='[{"name":"","dose":"","unit":"mg/m2"}]')
    cycle_number = models.IntegerField(default=1); total_cycles = models.IntegerField(null=True, blank=True)
    start_date = models.DateField(default=timezone.localdate)
    status = models.CharField(max_length=20, choices=[("planned","Planned"),("in_progress","In Progress"),("completed","Completed"),("discontinued","Discontinued")], default="planned")
    notes = models.TextField(blank=True)
    prescribed_by = models.ForeignKey("identity.User", on_delete=models.PROTECT, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    objects = TenantScopedManager()
    class Meta: db_table = "onc_chemo"; ordering = ["-start_date"]
    def __str__(self): return f"{self.protocol_name} Cycle {self.cycle_number} — {self.patient.full_name}"

class TumorMarker(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="tumor_markers")
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="tumor_markers")
    marker_name = models.CharField(max_length=200)
    value = models.DecimalField(max_digits=12, decimal_places=2); unit = models.CharField(max_length=50)
    reference_range = models.CharField(max_length=100, blank=True)
    measured_date = models.DateField(default=timezone.localdate)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    objects = TenantScopedManager()
    class Meta: db_table = "onc_marker"; ordering = ["-measured_date"]
    def __str__(self): return f"{self.marker_name}: {self.value} {self.unit} — {self.patient.full_name}"
