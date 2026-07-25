from rest_framework import serializers
from .models import BotConfig, WhatsAppConversation, WhatsAppMessage, VoiceCallLog


class BotConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = BotConfig
        exclude = ["tenant"]
        read_only_fields = ["created_at", "updated_at"]


class WhatsAppSendSerializer(serializers.Serializer):
    to_phone = serializers.CharField(required=True)
    message = serializers.CharField(required=True)


class VoiceCallSerializer(serializers.Serializer):
    to_phone = serializers.CharField(required=True)
    message = serializers.CharField(required=True)
    purpose = serializers.CharField(required=False, default="")


class AppointmentReminderSerializer(serializers.Serializer):
    patient_phone = serializers.CharField(required=True)
    patient_name = serializers.CharField(required=True)
    appointment_time = serializers.CharField(required=True)
    channel = serializers.ChoiceField(choices=["whatsapp", "voice"], default="whatsapp")


class WhatsAppMessageSerializer(serializers.ModelSerializer):
    direction_display = serializers.CharField(source="get_direction_display", read_only=True)

    class Meta:
        model = WhatsAppMessage
        fields = [
            "id", "direction", "direction_display", "message_type",
            "content", "media_url", "twilio_message_sid", "status",
            "is_bot_reply", "created_at",
        ]
        read_only_fields = fields


class WhatsAppConversationSerializer(serializers.ModelSerializer):
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = WhatsAppConversation
        fields = [
            "id", "customer_phone", "customer_name", "status",
            "is_bot_handled", "assigned_to", "message_count",
            "last_message", "unread_count", "last_message_at", "created_at",
        ]
        read_only_fields = fields

    def get_last_message(self, obj):
        msg = obj.messages.order_by("-created_at").first()
        if msg:
            return {"content": msg.content[:100], "direction": msg.direction, "created_at": msg.created_at.isoformat()}
        return None

    def get_unread_count(self, obj):
        return obj.messages.filter(direction="inbound").count()


class WhatsAppConversationDetailSerializer(serializers.ModelSerializer):
    messages = WhatsAppMessageSerializer(many=True, read_only=True)

    class Meta:
        model = WhatsAppConversation
        fields = "__all__"


class VoiceCallLogSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    direction_display = serializers.CharField(source="get_direction_display", read_only=True)

    class Meta:
        model = VoiceCallLog
        fields = [
            "id", "direction", "direction_display", "status", "status_display",
            "to_number", "from_number", "duration_seconds", "purpose",
            "twilio_call_sid", "recording_url", "transcription", "cost",
            "is_bot_call", "started_at", "ended_at", "created_at",
        ]
        read_only_fields = fields
