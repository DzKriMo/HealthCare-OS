from django.contrib import admin; from .models import EmergencyVisit
@admin.register(EmergencyVisit)
class ERVisitAdmin(admin.ModelAdmin): list_display = ["patient","arrival_date","triage_level","disposition"]
