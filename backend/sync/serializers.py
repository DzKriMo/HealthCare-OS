"""Serializers for sync engine."""
from rest_framework import serializers
from .models import DeviceRegistration, SyncOperation, SyncState, ConflictResolutionRule


class DeviceRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceRegistration
        fields = ["id", "device_name", "device_id", "platform", "is_active", "last_sync_at"]
        read_only_fields = ["id", "last_sync_at"]


class SyncOperationSerializer(serializers.ModelSerializer):
    class Meta:
        model = SyncOperation
        fields = [
            "id", "entity_type", "entity_id", "operation_type",
            "payload", "base_version", "sequence_number",
            "status", "server_version", "conflict_info",
            "client_timestamp", "created_at",
        ]


class PushRequestSerializer(serializers.Serializer):
    """Request body for push endpoint."""
    device_id = serializers.CharField()
    operations = serializers.JSONField(default=list)


class PullRequestSerializer(serializers.Serializer):
    """Request body for pull endpoint."""
    device_id = serializers.CharField()
    since_cursor = serializers.CharField(required=False, allow_blank=True, default="")


class ConflictRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConflictResolutionRule
        fields = ["id", "entity_type", "strategy", "merge_safe_fields"]
