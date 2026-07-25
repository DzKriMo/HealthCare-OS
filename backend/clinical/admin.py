from django.contrib import admin
from .models import Encounter, Diagnosis, Referral, VitalSigns, Vaccination, FamilyHistory, SocialHistory

@admin.register(Encounter)
class EncounterAdmin(admin.ModelAdmin):
    list_display = ["patient","encounter_date","status","practitioner"]
@admin.register(Diagnosis)
class DiagnosisAdmin(admin.ModelAdmin):
    list_display = ["patient","icd_code","description","diagnosis_type","is_active"]
@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    list_display = ["patient","specialist_name","specialty","urgency","status"]
@admin.register(VitalSigns)
class VitalSignsAdmin(admin.ModelAdmin):
    list_display = ["patient","heart_rate","systolic_bp","bmi","recorded_at"]
@admin.register(Vaccination)
class VaccinationAdmin(admin.ModelAdmin):
    list_display = ["patient","vaccine_name","dose_number","administered_date"]
@admin.register(FamilyHistory)
class FamilyHistoryAdmin(admin.ModelAdmin):
    list_display = ["patient","relationship","condition"]
@admin.register(SocialHistory)
class SocialHistoryAdmin(admin.ModelAdmin):
    list_display = ["patient","smoking_status","alcohol_use","exercise_frequency"]
