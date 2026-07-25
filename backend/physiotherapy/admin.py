from django.contrib import admin; from .models import PhysiotherapySession
@admin.register(PhysiotherapySession)
class PhysioSessionAdmin(admin.ModelAdmin): list_display = ["patient","session_date","treatment_type"]
