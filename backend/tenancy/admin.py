"""
Django Admin for tenant management.
"""
from django.contrib import admin
from .models import Tenant, TenantSettings


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "subscription_status", "is_active", "created_at"]
    list_filter = ["is_active", "subscription_status"]
    search_fields = ["name", "slug"]
    prepopulated_fields = {"slug": ["name"]}
    readonly_fields = ["created_at", "updated_at"]


@admin.register(TenantSettings)
class TenantSettingsAdmin(admin.ModelAdmin):
    list_display = ["tenant", "timezone", "language", "default_currency"]
    search_fields = ["tenant__name"]

from .models import ProductEdition, CompliancePolicy, OnboardingStep

@admin.register(ProductEdition)
class ProductEditionAdmin(admin.ModelAdmin): list_display = ["name","max_users","max_branches","monthly_price","is_active"]
@admin.register(CompliancePolicy)
class CompliancePolicyAdmin(admin.ModelAdmin): list_display = ["tenant","clinical_record_retention_days","require_signature_on_prescriptions"]
@admin.register(OnboardingStep)
class OnboardingStepAdmin(admin.ModelAdmin): list_display = ["tenant","step_name","is_completed","display_order"]
