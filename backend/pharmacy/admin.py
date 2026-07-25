from django.contrib import admin
from .models import Prescription, DispenseRecord, ControlledSubstanceLog

@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ["drug_name", "patient", "status", "prescribed_by", "is_controlled"]
    list_filter = ["status", "is_controlled", "tenant"]

@admin.register(DispenseRecord)
class DispenseRecordAdmin(admin.ModelAdmin):
    list_display = ["prescription", "patient", "quantity", "dispensed_by", "dispensed_at"]

@admin.register(ControlledSubstanceLog)
class ControlledSubstanceLogAdmin(admin.ModelAdmin):
    list_display = ["prescription", "witness", "count_verified", "logged_at"]
