"""Emergency/Urgent Care models — triage, chief complaint, disposition."""
import uuid; from django.db import models; from django.utils import timezone
from tenancy.models import Tenant; from tenancy.managers import TenantScopedManager; from patients.models import Patient

class EmergencyVisit(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="er_visits")
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="er_visits")
    arrival_date = models.DateTimeField(default=timezone.now)
    triage_level = models.IntegerField(choices=[(1,"1 — Immediate"),(2,"2 — Emergent"),(3,"3 — Urgent"),(4,"4 — Semi-Urgent"),(5,"5 — Non-Urgent")], help_text="ESI Triage Level")
    chief_complaint = models.TextField()
    mode_of_arrival = models.CharField(max_length=30, choices=[("self","Self/Walk-in"),("ambulance","Ambulance"),("transfer","Transfer")], default="self")
    disposition = models.CharField(max_length=30, choices=[("admitted","Admitted"),("discharged","Discharged"),("transferred","Transferred"),("ama","Left AMA"),("expired","Expired")], blank=True)
    disposition_date = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    practitioner = models.ForeignKey("identity.User", on_delete=models.PROTECT, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    objects = TenantScopedManager()
    class Meta: db_table = "er_visit"; ordering = ["-arrival_date"]
    def __str__(self): return f"ER Visit ESI {self.triage_level} — {self.patient.full_name}"
