"""Pediatrics models — growth charts, vaccinations, milestones."""
import uuid
from django.db import models
from django.utils import timezone
from tenancy.models import Tenant
from tenancy.managers import TenantScopedManager
from patients.models import Patient


class GrowthRecord(models.Model):
    """Height, weight, head circumference at a point in time."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="growth_records")
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="growth_records")

    measured_date = models.DateField(default=timezone.localdate)
    height_cm = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    weight_kg = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    head_circumference_cm = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    bmi = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)

    # Percentiles (calculated)
    height_percentile = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    weight_percentile = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    bmi_percentile = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)

    recorded_by = models.ForeignKey("identity.User", on_delete=models.PROTECT, null=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = TenantScopedManager()

    class Meta:
        db_table = "peds_growth"
        ordering = ["-measured_date"]
        indexes = [models.Index(fields=["patient"]), models.Index(fields=["measured_date"])]

    def __str__(self): return f"Growth {self.measured_date} — {self.patient.full_name}"


class VaccinationSchedule(models.Model):
    """Age-based vaccination schedule — due/overdue tracking."""

    class Status(models.TextChoices):
        DUE = "due", "Due"
        ADMINISTERED = "administered", "Administered"
        OVERDUE = "overdue", "Overdue"
        DECLINED = "declined", "Declined"
        CONTRAINDICATED = "contraindicated", "Contraindicated"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="vax_schedules")
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="vax_schedules")

    vaccine_name = models.CharField(max_length=300)
    recommended_age_months = models.IntegerField(help_text="Age in months when vaccine is recommended.")
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DUE)
    administered_date = models.DateField(null=True, blank=True)
    vaccination_record = models.ForeignKey("clinical.Vaccination", on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    objects = TenantScopedManager()

    class Meta:
        db_table = "peds_vax_schedule"
        ordering = ["recommended_age_months", "vaccine_name"]

    def __str__(self): return f"{self.vaccine_name} — {self.patient.full_name} ({self.status})"


class DevelopmentalMilestone(models.Model):
    """Developmental milestone tracking."""

    class AgeGroup(models.TextChoices):
        MONTHS_2 = "2m", "2 Months"
        MONTHS_4 = "4m", "4 Months"
        MONTHS_6 = "6m", "6 Months"
        MONTHS_9 = "9m", "9 Months"
        MONTHS_12 = "12m", "12 Months"
        MONTHS_18 = "18m", "18 Months"
        YEARS_2 = "2y", "2 Years"
        YEARS_3 = "3y", "3 Years"
        YEARS_4 = "4y", "4 Years"
        YEARS_5 = "5y", "5 Years"

    class Domain(models.TextChoices):
        GROSS_MOTOR = "gross_motor", "Gross Motor"
        FINE_MOTOR = "fine_motor", "Fine Motor"
        LANGUAGE = "language", "Language"
        SOCIAL = "social", "Social-Emotional"
        COGNITIVE = "cognitive", "Cognitive"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="milestones")
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="milestones")

    age_group = models.CharField(max_length=10, choices=AgeGroup.choices)
    domain = models.CharField(max_length=20, choices=Domain.choices)
    milestone_name = models.CharField(max_length=300)
    is_achieved = models.BooleanField(default=False)
    achieved_date = models.DateField(null=True, blank=True)
    is_delayed = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    recorded_by = models.ForeignKey("identity.User", on_delete=models.PROTECT, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = TenantScopedManager()

    class Meta:
        db_table = "peds_milestone"
        ordering = ["age_group", "domain"]

    def __str__(self): return f"{self.milestone_name} ({self.age_group}) — {self.patient.full_name}"
