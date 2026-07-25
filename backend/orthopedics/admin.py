from django.contrib import admin
from .models import JointAssessment, FractureRecord, PhysiotherapyPlan

@admin.register(JointAssessment)
class JointAdmin(admin.ModelAdmin): list_display = ["patient","joint","side","assessment_date"]
@admin.register(FractureRecord)
class FractureAdmin(admin.ModelAdmin): list_display = ["patient","bone","fracture_type","healing_status"]
@admin.register(PhysiotherapyPlan)
class PhysioAdmin(admin.ModelAdmin): list_display = ["patient","name","is_active","start_date"]
