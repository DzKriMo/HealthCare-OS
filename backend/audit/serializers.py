"""Serializers for audit events."""
from rest_framework import serializers
from .models import AuditEvent


class AuditEventSerializer(serializers.ModelSerializer):
    tenant_slug = serializers.CharField(source="tenant.slug", read_only=True)

    class Meta:
        model = AuditEvent
        fields = [
            "id", "tenant", "tenant_slug",
            "actor", "actor_display",
            "entity_type", "entity_id", "entity_display",
            "action", "before_value", "after_value",
            "correlation_id", "ip_address",
            "is_sensitive", "created_at",
        ]


class AuditExportSerializer(serializers.Serializer):
    """Query params for audit export."""
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)
    entity_type = serializers.CharField(required=False)
    entity_id = serializers.CharField(required=False)
    actor_id = serializers.UUIDField(required=False)
    action = serializers.CharField(required=False)
    format = serializers.ChoiceField(choices=["csv", "json"], default="csv")
