"""
Imaging/Radiology models — Sprint B4.
ImagingStudy → ImagingSeries → ImagingImage, RadiologyReport with sign workflow.
"""
import uuid
from django.db import models
from django.utils import timezone
from tenancy.models import Tenant
from tenancy.managers import TenantScopedManager
from patients.models import Patient


class ImagingStudy(models.Model):
    """A complete imaging study (exam) for a patient."""

    class Modality(models.TextChoices):
        XRAY = "xray", "X-Ray"
        CT = "ct", "CT Scan"
        MRI = "mri", "MRI"
        ULTRASOUND = "ultrasound", "Ultrasound"
        MAMMOGRAPHY = "mammography", "Mammography"
        NUCLEAR = "nuclear", "Nuclear Medicine"
        DEXA = "dexa", "DEXA / Bone Density"
        OTHER = "other", "Other"

    class Status(models.TextChoices):
        SCHEDULED = "scheduled", "Scheduled"
        PERFORMED = "performed", "Performed"
        REPORTING = "reporting", "Reporting"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="imaging_studies")
    patient = models.ForeignKey(Patient, on_delete=models.PROTECT, related_name="imaging_studies")
    appointment = models.ForeignKey("scheduling.Appointment", on_delete=models.SET_NULL, null=True, blank=True)

    study_uid = models.CharField(max_length=200, unique=True, blank=True, help_text="DICOM Study Instance UID.")
    accession_number = models.CharField(max_length=100, blank=True)
    modality = models.CharField(max_length=20, choices=Modality.choices)
    body_part = models.CharField(max_length=200, blank=True, help_text="e.g. Chest, Brain, Left Knee")
    protocol = models.CharField(max_length=300, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SCHEDULED)
    priority = models.CharField(max_length=10, choices=[("routine","Routine"),("urgent","Urgent"),("stat","STAT")], default="routine")
    reason = models.TextField(blank=True, help_text="Clinical indication for the study.")

    ordered_by = models.ForeignKey("identity.User", on_delete=models.PROTECT, null=True, related_name="ordered_studies")
    performed_by = models.ForeignKey("identity.User", on_delete=models.PROTECT, null=True, blank=True, related_name="performed_studies")
    performed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = TenantScopedManager()

    class Meta:
        db_table = "imaging_study"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["tenant"]), models.Index(fields=["patient"]), models.Index(fields=["modality"]),
                   models.Index(fields=["status"]), models.Index(fields=["study_uid"])]

    def __str__(self):
        return f"{self.get_modality_display()} — {self.body_part} ({self.patient.full_name})"


class ImagingSeries(models.Model):
    """A series within an imaging study (DICOM series)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    study = models.ForeignKey(ImagingStudy, on_delete=models.CASCADE, related_name="series")
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)

    series_uid = models.CharField(max_length=200, blank=True, help_text="DICOM Series Instance UID.")
    series_number = models.IntegerField(default=1)
    modality = models.CharField(max_length=20, blank=True)
    description = models.CharField(max_length=500, blank=True)
    body_part = models.CharField(max_length=200, blank=True)
    image_count = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    objects = TenantScopedManager()

    class Meta:
        db_table = "imaging_series"
        ordering = ["series_number"]
        verbose_name_plural = "imaging series"

    def __str__(self): return f"Series {self.series_number} — {self.description or self.modality}"


class ImagingImage(models.Model):
    """Individual image/slice within a series."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    series = models.ForeignKey(ImagingSeries, on_delete=models.CASCADE, related_name="images")
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)

    sop_instance_uid = models.CharField(max_length=200, blank=True, help_text="DICOM SOP Instance UID.")
    image_number = models.IntegerField(default=1)
    file_path = models.CharField(max_length=1000, blank=True, help_text="Object storage path.")
    mime_type = models.CharField(max_length=50, default="application/dicom")
    file_size = models.BigIntegerField(default=0)
    width = models.IntegerField(null=True, blank=True)
    height = models.IntegerField(null=True, blank=True)
    slice_location = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    window_center = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    window_width = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)

    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "imaging_image"
        ordering = ["image_number"]

    def __str__(self): return f"Image {self.image_number} — Series {self.series.series_number}"


class RadiologyReport(models.Model):
    """Radiologist's report for an imaging study."""

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        DICTATED = "dictated", "Dictated"
        TRANSCRIBED = "transcribed", "Transcribed"
        REVIEWED = "reviewed", "Reviewed"
        SIGNED = "signed", "Signed"
        AMENDED = "amended", "Amended"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="radiology_reports")
    study = models.OneToOneField(ImagingStudy, on_delete=models.CASCADE, related_name="report")

    findings = models.TextField(blank=True, help_text="Detailed imaging findings.")
    impression = models.TextField(blank=True, help_text="Summary impression / conclusion.")
    recommendations = models.TextField(blank=True, help_text="Follow-up recommendations.")
    comparison_study = models.ForeignKey(ImagingStudy, on_delete=models.SET_NULL, null=True, blank=True,
                                         related_name="compared_reports", help_text="Prior study for comparison.")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)

    author = models.ForeignKey("identity.User", on_delete=models.PROTECT, null=True, related_name="radiology_reports")
    signed_by = models.ForeignKey("identity.User", on_delete=models.PROTECT, null=True, blank=True, related_name="signed_reports")
    signed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = TenantScopedManager()

    class Meta:
        db_table = "imaging_report"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["tenant"]), models.Index(fields=["study"]), models.Index(fields=["status"])]

    def __str__(self): return f"Report: {self.study}"
