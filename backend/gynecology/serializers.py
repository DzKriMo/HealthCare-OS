from rest_framework import serializers
from .models import OBHistory, PapSmear, AntenatalVisit

class OBHistorySerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    class Meta:
        model = OBHistory
        fields = ["id","patient","gravida","para","abortus","lmp","edd","notes"]
        read_only_fields = ["id"]

class PapSmearSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    class Meta:
        model = PapSmear
        fields = ["id","patient","performed_date","result","hpv_co_test","hpv_positive","follow_up_recommended","notes"]
        read_only_fields = ["id","performed_by"]

class AntenatalSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    class Meta:
        model = AntenatalVisit
        fields = ["id","patient","visit_date","gestational_weeks","weight_kg","bp_systolic","bp_diastolic","fundal_height_cm","fetal_hr","fetal_movement","ultrasound_findings","notes"]
        read_only_fields = ["id","practitioner"]
