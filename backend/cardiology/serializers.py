from rest_framework import serializers
from .models import ECGRecord, EchoReport, BPReading, CVRiskScore


class ECGSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    patient_name = serializers.CharField(source="patient.full_name", read_only=True)
    class Meta:
        model = ECGRecord
        fields = ["id","patient","patient_name","performed_date","heart_rate","rhythm","pr_interval","qrs_duration","qt_interval","findings","interpretation","is_abnormal"]
        read_only_fields = ["id","performed_by"]

class EchoSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    patient_name = serializers.CharField(source="patient.full_name", read_only=True)
    class Meta:
        model = EchoReport
        fields = ["id","patient","patient_name","study_date","lvef","lv_ed_diameter","la_diameter","rv_function","valve_findings","findings","conclusion"]
        read_only_fields = ["id","performed_by"]

class BPReadingSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    class Meta:
        model = BPReading
        fields = ["id","patient","systolic","diastolic","pulse","recorded_at","notes"]
        read_only_fields = ["id","recorded_at"]

class CVRiskSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    patient_name = serializers.CharField(source="patient.full_name", read_only=True)
    class Meta:
        model = CVRiskScore
        fields = ["id","patient","patient_name","score_type","risk_percentage","risk_category","calculated_date","factors"]
        read_only_fields = ["id"]
