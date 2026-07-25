from rest_framework import serializers
from .models import AudiologyExam, EndoscopyRecord

class AudiologySerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    class Meta:
        model = AudiologyExam
        fields = ["id","patient","exam_date","test_type","thresholds_od","thresholds_os","hearing_loss_type","hearing_loss_severity","findings","recommendations"]
        read_only_fields = ["id","performed_by"]

class EndoscopySerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    class Meta:
        model = EndoscopyRecord
        fields = ["id","patient","procedure_date","endoscopy_type","findings","diagnosis","images_paths","notes"]
        read_only_fields = ["id","performed_by"]
