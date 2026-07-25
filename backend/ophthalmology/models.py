"""Ophthalmology models — Sprint B6. Eye exams, vision tests, lens prescriptions."""
import uuid
from django.db import models
from django.utils import timezone
from tenancy.models import Tenant
from tenancy.managers import TenantScopedManager
from patients.models import Patient


class EyeExam(models.Model):
    """A comprehensive eye examination."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="eye_exams")
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="eye_exams")

    exam_date = models.DateField(default=timezone.localdate)
    reason = models.TextField(blank=True)

    # Visual acuity (OD = right eye, OS = left eye, OU = both)
    va_od_unaided = models.CharField(max_length=20, blank=True, help_text="e.g. 20/20")
    va_os_unaided = models.CharField(max_length=20, blank=True)
    va_od_best = models.CharField(max_length=20, blank=True, help_text="Best corrected.")
    va_os_best = models.CharField(max_length=20, blank=True)

    # Refraction
    refraction_od_sphere = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    refraction_od_cylinder = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    refraction_od_axis = models.IntegerField(null=True, blank=True)
    refraction_os_sphere = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    refraction_os_cylinder = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    refraction_os_axis = models.IntegerField(null=True, blank=True)

    # Intraocular pressure (mmHg)
    iop_od = models.IntegerField(null=True, blank=True)
    iop_os = models.IntegerField(null=True, blank=True)

    # Slit lamp findings
    slit_lamp_findings = models.TextField(blank=True)
    fundus_findings = models.TextField(blank=True)

    assessment = models.TextField(blank=True)
    plan = models.TextField(blank=True)

    practitioner = models.ForeignKey("identity.User", on_delete=models.PROTECT, null=True, related_name="eye_exams")
    created_at = models.DateTimeField(auto_now_add=True)

    objects = TenantScopedManager()

    class Meta:
        db_table = "ophth_exam"
        ordering = ["-exam_date"]
        indexes = [models.Index(fields=["patient"]), models.Index(fields=["exam_date"])]

    def __str__(self): return f"Eye Exam {self.exam_date} — {self.patient.full_name}"


class VisionTest(models.Model):
    """Additional vision tests — color, visual field, Amsler grid."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    exam = models.ForeignKey(EyeExam, on_delete=models.CASCADE, related_name="vision_tests")
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)

    test_type = models.CharField(max_length=30, choices=[
        ("color_vision","Color Vision"),("visual_field","Visual Field"),
        ("amsler_grid","Amsler Grid"),("other","Other")])
    result_od = models.TextField(blank=True, help_text="Right eye result.")
    result_os = models.TextField(blank=True, help_text="Left eye result.")
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "ophth_vision_test"

    def __str__(self): return f"{self.test_type} — {self.exam}"


class LensPrescription(models.Model):
    """Eyeglass or contact lens prescription."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="lens_prescriptions")
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="lens_prescriptions")
    exam = models.ForeignKey(EyeExam, on_delete=models.SET_NULL, null=True, blank=True)

    prescription_type = models.CharField(max_length=20, choices=[("glasses","Glasses"),("contacts","Contact Lenses")], default="glasses")
    od_sphere = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    od_cylinder = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    od_axis = models.IntegerField(null=True, blank=True)
    od_add = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    os_sphere = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    os_cylinder = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    os_axis = models.IntegerField(null=True, blank=True)
    os_add = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    pd = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True, help_text="Pupillary distance in mm.")
    notes = models.TextField(blank=True)
    prescribed_date = models.DateField(default=timezone.localdate)
    prescribed_by = models.ForeignKey("identity.User", on_delete=models.PROTECT, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = TenantScopedManager()

    class Meta:
        db_table = "ophth_prescription"
        ordering = ["-prescribed_date"]

    def __str__(self): return f"Rx {self.prescription_type} — {self.patient.full_name}"
