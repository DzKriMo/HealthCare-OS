from django.contrib import admin
from .models import WebhookEndpoint, WebhookDelivery

@admin.register(WebhookEndpoint)
class WebhookEndpointAdmin(admin.ModelAdmin):
    list_display = ["name", "url", "tenant", "is_active"]

@admin.register(WebhookDelivery)
class WebhookDeliveryAdmin(admin.ModelAdmin):
    list_display = ["webhook", "event_type", "status", "attempts", "created_at"]

from .models import PaymentProviderConfig, CalendarProviderConfig, CommunicationProviderConfig

@admin.register(PaymentProviderConfig)
class PaymentConfigAdmin(admin.ModelAdmin): list_display = ["tenant","provider","is_enabled","is_test_mode"]

@admin.register(CalendarProviderConfig)
class CalendarConfigAdmin(admin.ModelAdmin): list_display = ["tenant","provider","is_enabled","sync_direction"]

@admin.register(CommunicationProviderConfig)
class CommConfigAdmin(admin.ModelAdmin): list_display = ["tenant","channel","provider_name","is_enabled"]

from .models import InsuranceClearinghouseConfig, EDIClaimSubmission, EligibilityCheck, AccountingProviderConfig, GovernmentConnectorConfig

@admin.register(InsuranceClearinghouseConfig)
class ClearinghouseAdmin(admin.ModelAdmin): list_display = ["name","tenant","is_enabled"]
@admin.register(EDIClaimSubmission)
class EDIClaimAdmin(admin.ModelAdmin): list_display = ["claim_number","patient","status","submitted_amount"]
@admin.register(EligibilityCheck)
class EligibilityAdmin(admin.ModelAdmin): list_display = ["patient","status","check_date"]
@admin.register(AccountingProviderConfig)
class AccountingAdmin(admin.ModelAdmin): list_display = ["tenant","provider","is_enabled"]
@admin.register(GovernmentConnectorConfig)
class GovConnectorAdmin(admin.ModelAdmin): list_display = ["tenant","connector_type","is_enabled"]

from .models import Plugin, PluginInstallation, PluginReview

@admin.register(Plugin)
class PluginAdmin(admin.ModelAdmin): list_display = ["name","version","author","category","pricing_type","is_certified","install_count"]
@admin.register(PluginInstallation)
class PluginInstallAdmin(admin.ModelAdmin): list_display = ["plugin","tenant","is_enabled","installed_at"]
@admin.register(PluginReview)
class PluginReviewAdmin(admin.ModelAdmin): list_display = ["plugin","tenant","rating","created_at"]
