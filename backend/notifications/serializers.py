"""Serializers for notifications."""
from rest_framework import serializers
from .models import NotificationTemplate, NotificationEvent, NotificationChannelConfig


class NotificationTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationTemplate
        fields = [
            "id", "name", "event_type", "channel",
            "subject", "body_text", "body_html",
            "available_variables", "language", "is_active",
        ]
        read_only_fields = ["id"]


class NotificationEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationEvent
        fields = [
            "id", "event_type", "channel",
            "recipient_email", "recipient_phone", "recipient_name",
            "subject", "status", "error_message",
            "sent_at", "delivered_at", "created_at",
        ]
        read_only_fields = ["id", "status", "sent_at", "delivered_at", "created_at"]


class NotificationSendSerializer(serializers.Serializer):
    """Manually trigger a notification."""
    event_type = serializers.CharField()
    channel = serializers.ChoiceField(choices=["email", "sms", "whatsapp", "push"])
    recipient_email = serializers.EmailField(required=False, allow_blank=True)
    recipient_phone = serializers.CharField(required=False, allow_blank=True)
    recipient_name = serializers.CharField(required=False, allow_blank=True)
    context = serializers.JSONField(required=False, default=dict)


class ChannelConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationChannelConfig
        fields = [
            "email_enabled", "email_from_address", "email_from_name",
            "sms_enabled", "sms_provider", "sms_from_number",
            "whatsapp_enabled", "whatsapp_from_number",
            "push_enabled", "max_sms_per_day", "max_email_per_hour",
        ]
