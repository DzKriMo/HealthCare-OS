from django.contrib import admin; from .models import DialysisSession
@admin.register(DialysisSession)
class DialysisSessionAdmin(admin.ModelAdmin): list_display = ["patient","session_date","dialysis_type","fluid_removed_ml"]
