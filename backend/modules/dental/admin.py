from django.contrib import admin
from .models import ToothChart, Tooth, ToothProcedure, Implant, Crown, DentalTreatmentPlan, TreatmentPlanPhase, PlannedProcedure

@admin.register(ToothChart)
class ToothChartAdmin(admin.ModelAdmin):
    list_display = ["patient", "tenant"]

@admin.register(Tooth)
class ToothAdmin(admin.ModelAdmin):
    list_display = ["fdi_number", "condition", "chart"]

@admin.register(ToothProcedure)
class ToothProcedureAdmin(admin.ModelAdmin):
    list_display = ["patient", "procedure_type", "tooth", "performed_at"]

@admin.register(Implant)
class ImplantAdmin(admin.ModelAdmin):
    list_display = ["patient", "tooth", "brand", "placement_date"]

@admin.register(Crown)
class CrownAdmin(admin.ModelAdmin):
    list_display = ["patient", "tooth", "material", "cementation_date"]

@admin.register(DentalTreatmentPlan)
class DentalTreatmentPlanAdmin(admin.ModelAdmin):
    list_display = ["name", "patient", "status", "estimated_total"]

@admin.register(TreatmentPlanPhase)
class TreatmentPlanPhaseAdmin(admin.ModelAdmin):
    list_display = ["name", "plan", "order", "is_completed"]

@admin.register(PlannedProcedure)
class PlannedProcedureAdmin(admin.ModelAdmin):
    list_display = ["procedure_type", "phase", "priority", "is_completed"]
