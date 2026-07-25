from rest_framework import serializers
from .models import VideoConsultation, ChatRoom, ChatMessage


class VideoConsultationSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.full_name", read_only=True)
    practitioner_name = serializers.CharField(source="practitioner.full_name", read_only=True)

    class Meta:
        model = VideoConsultation
        fields = [
            "id", "appointment", "patient", "patient_name",
            "practitioner", "practitioner_name",
            "status", "scheduled_at", "started_at", "ended_at",
            "meeting_url", "room_name", "notes", "cancellation_reason",
            "created_by", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "room_name", "created_by", "created_at", "updated_at", "started_at", "ended_at"]

    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user
        validated_data["tenant"] = self.context["request"].tenant
        validated_data["room_name"] = f"room-{uuid.uuid4().hex[:12]}"
        import uuid
        return VideoConsultation.objects.create(**validated_data)


class VideoConsultationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoConsultation
        fields = ["appointment", "patient", "practitioner", "scheduled_at", "notes"]


class ChatRoomSerializer(serializers.ModelSerializer):
    participant_names = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = ChatRoom
        fields = ["id", "consultation", "participants", "participant_names", "last_message", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_participant_names(self, obj):
        return [u.full_name for u in obj.participants.all()]

    def get_last_message(self, obj):
        msg = obj.messages.order_by("-created_at").first()
        if msg:
            return {
                "content": msg.content[:100],
                "sender_name": msg.sender.full_name,
                "created_at": msg.created_at.isoformat(),
            }
        return None


class ChatMessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source="sender.full_name", read_only=True)

    class Meta:
        model = ChatMessage
        fields = ["id", "room", "sender", "sender_name", "content", "attachment_url", "read_at", "created_at"]
        read_only_fields = ["id", "sender", "read_at", "created_at"]

    def create(self, validated_data):
        validated_data["sender"] = self.context["request"].user
        return ChatMessage.objects.create(**validated_data)


class ChatMessageCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ["room", "content", "attachment_url"]
