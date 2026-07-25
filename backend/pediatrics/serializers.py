from rest_framework import serializers
from .models import GrowthRecord, VaccinationSchedule, DevelopmentalMilestone


class GrowthRecordSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    class Meta:
        model = GrowthRecord
        fields = ["id","patient","measured_date","height_cm","weight_kg","head_circumference_cm","bmi","height_percentile","weight_percentile","bmi_percentile","notes"]
        read_only_fields = ["id","recorded_by","created_at"]

class VaxScheduleSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    class Meta:
        model = VaccinationSchedule
        fields = ["id","patient","vaccine_name","recommended_age_months","due_date","status","administered_date","notes"]
        read_only_fields = ["id"]

class MilestoneSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    class Meta:
        model = DevelopmentalMilestone
        fields = ["id","patient","age_group","domain","milestone_name","is_achieved","achieved_date","is_delayed","notes"]
        read_only_fields = ["id","recorded_by"]
