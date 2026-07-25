from rest_framework import serializers; from .models import DialysisSession

class DialysisSessionSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True); weight_loss_kg = serializers.FloatField(read_only=True)
    class Meta:
        model = DialysisSession
        fields = ["id","patient","session_date","dialysis_type","duration_minutes","pre_weight_kg","post_weight_kg","weight_loss_kg","fluid_removed_ml","pre_bp_systolic","pre_bp_diastolic","post_bp_systolic","post_bp_diastolic","access_site","access_site_condition","complications","notes"]
        read_only_fields = ["id","practitioner"]
