from rest_framework import serializers; from .models import EmergencyVisit

class ERVisitSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True); patient_name = serializers.CharField(source="patient.full_name", read_only=True)
    class Meta:
        model = EmergencyVisit
        fields = ["id","patient","patient_name","arrival_date","triage_level","chief_complaint","mode_of_arrival","disposition","disposition_date","notes"]
        read_only_fields = ["id","practitioner"]
