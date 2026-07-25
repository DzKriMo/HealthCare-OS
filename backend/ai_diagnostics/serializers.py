from rest_framework import serializers
from .models import AISettings, AISuggestion, AIAuditLog


class AISettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = AISettings
        fields = [
            "provider", "api_key", "api_endpoint", "model",
            "temperature", "max_tokens", "enabled_features",
            "require_human_review", "created_at", "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]
        extra_kwargs = {"api_key": {"write_only": True}}


class AISuggestionSerializer(serializers.ModelSerializer):
    suggestion_type_display = serializers.CharField(source="get_suggestion_type_display", read_only=True)
    patient_name = serializers.CharField(source="patient.full_name", read_only=True)

    class Meta:
        model = AISuggestion
        fields = [
            "id", "suggestion_type", "suggestion_type_display",
            "patient", "patient_name", "encounter",
            "input_data", "output_data", "confidence",
            "accepted", "accepted_by", "reviewed_at",
            "latency_ms", "model_used", "is_fallback", "error",
            "created_by", "created_at",
        ]
        read_only_fields = [
            "id", "accepted", "accepted_by", "reviewed_at",
            "latency_ms", "model_used", "is_fallback", "error",
            "created_by", "created_at",
        ]


class ICD10SuggestionInputSerializer(serializers.Serializer):
    diagnosis_text = serializers.CharField(required=True)
    context = serializers.JSONField(required=False)


class SOAPDraftInputSerializer(serializers.Serializer):
    subjective = serializers.CharField(required=False, default="")
    objective = serializers.CharField(required=False, default="")
    assessment = serializers.CharField(required=False, default="")
    vitals = serializers.JSONField(required=False)


class DrugInteractionInputSerializer(serializers.Serializer):
    medications = serializers.ListField(child=serializers.DictField())


class SymptomAnalysisInputSerializer(serializers.Serializer):
    symptoms = serializers.CharField(required=True)
    vitals = serializers.JSONField(required=False)


class TreatmentPlanInputSerializer(serializers.Serializer):
    diagnosis = serializers.CharField(required=True)
    patient_info = serializers.JSONField(required=False)


class CPTInputSerializer(serializers.Serializer):
    procedure_description = serializers.CharField(required=True)


class PrescriptionDraftInputSerializer(serializers.Serializer):
    diagnosis = serializers.CharField(required=True)
    patient_info = serializers.JSONField(required=False)


class SuggestionFeedbackSerializer(serializers.Serializer):
    accepted = serializers.BooleanField(required=True)


class AIAuditLogSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.full_name", read_only=True)
    action_display = serializers.CharField(source="get_action_display", read_only=True)

    class Meta:
        model = AIAuditLog
        fields = [
            "id", "user", "user_name", "action", "action_display",
            "suggestion", "details", "ip_address", "created_at",
        ]
        read_only_fields = fields
