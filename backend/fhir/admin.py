from django.contrib import admin
from .models import SMARTonFHIRConfig, FHIRAppRegistration

@admin.register(SMARTonFHIRConfig)
class SMARTConfigAdmin(admin.ModelAdmin): list_display = ["tenant","is_enabled"]

@admin.register(FHIRAppRegistration)
class FHIRAppAdmin(admin.ModelAdmin): list_display = ["app_name","client_id","tenant","is_active"]
