from django.contrib import admin
from .models import AuditEvent

@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = ["created_at", "actor_display", "action", "entity_type", "entity_id", "tenant"]
    list_filter = ["action", "entity_type", "tenant", "created_at"]
    search_fields = ["actor_display", "entity_id", "entity_display"]
    readonly_fields = ["id", "tenant", "actor", "actor_display", "entity_type", "entity_id",
                       "entity_display", "action", "before_value", "after_value",
                       "correlation_id", "ip_address", "is_sensitive", "created_at"]
    date_hierarchy = "created_at"
