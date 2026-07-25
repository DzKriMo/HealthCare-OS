"""Django Admin for patient domain models."""
from django.contrib import admin
from .models import (
    Patient, MedicalHistory, Allergy, CurrentMedication,
    InsurancePolicy, EmergencyContact, ConsentRecord,
)


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ["display_id", "first_name", "last_name", "tenant", "gender", "date_of_birth", "is_active"]
    list_filter = ["is_active", "gender", "tenant"]
    search_fields = ["first_name", "last_name", "display_id", "phone_primary", "email"]
    readonly_fields = ["id", "display_id", "registration_date", "created_at", "updated_at"]


@admin.register(MedicalHistory)
class MedicalHistoryAdmin(admin.ModelAdmin):
    list_display = ["patient", "category", "condition", "is_active", "recorded_at"]
    list_filter = ["category", "is_active"]


@admin.register(Allergy)
class AllergyAdmin(admin.ModelAdmin):
    list_display = ["patient", "substance", "severity", "status"]
    list_filter = ["severity", "status"]


@admin.register(CurrentMedication)
class CurrentMedicationAdmin(admin.ModelAdmin):
    list_display = ["patient", "drug_name", "dosage", "is_active", "start_date"]
    list_filter = ["is_active"]


@admin.register(InsurancePolicy)
class InsurancePolicyAdmin(admin.ModelAdmin):
    list_display = ["patient", "provider", "policy_number", "coverage_type", "is_verified"]
    list_filter = ["coverage_type", "is_verified"]


@admin.register(EmergencyContact)
class EmergencyContactAdmin(admin.ModelAdmin):
    list_display = ["patient", "name", "relationship", "phone_primary", "is_primary"]


@admin.register(ConsentRecord)
class ConsentRecordAdmin(admin.ModelAdmin):
    list_display = ["patient", "consent_type", "form_name", "status", "granted_at"]
    list_filter = ["consent_type", "status"]
