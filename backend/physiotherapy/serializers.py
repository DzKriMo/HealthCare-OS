from rest_framework import serializers; from .models import PhysiotherapySession

class PhysioSessionSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    class Meta:
        model = PhysiotherapySession
        fields = ["id","patient","session_date","treatment_type","exercises_performed","subjective","objective","assessment","plan","pain_pre","pain_post","duration_minutes"]
        read_only_fields = ["id","practitioner"]
