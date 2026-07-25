from django.contrib import admin
from .models import NotificationTemplate, NotificationEvent, NotificationChannelConfig

@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ["name", "event_type", "channel", "tenant", "is_active"]
    list_filter = ["event_type", "channel", "is_active"]

@admin.register(NotificationEvent)
class NotificationEventAdmin(admin.ModelAdmin):
    list_display = ["event_type", "channel", "recipient_name", "status", "sent_at"]
    list_filter = ["status", "channel", "event_type"]

@admin.register(NotificationChannelConfig)
class NotificationChannelConfigAdmin(admin.ModelAdmin):
    list_display = ["tenant", "email_enabled", "sms_enabled", "whatsapp_enabled"]
