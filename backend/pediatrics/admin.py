from django.contrib import admin
from .models import GrowthRecord, VaccinationSchedule, DevelopmentalMilestone

@admin.register(GrowthRecord)
class GrowthRecordAdmin(admin.ModelAdmin): list_display = ["patient","measured_date","height_cm","weight_kg","bmi_percentile"]
@admin.register(VaccinationSchedule)
class VaxScheduleAdmin(admin.ModelAdmin): list_display = ["patient","vaccine_name","status","due_date"]
@admin.register(DevelopmentalMilestone)
class MilestoneAdmin(admin.ModelAdmin): list_display = ["patient","age_group","domain","milestone_name","is_achieved"]
