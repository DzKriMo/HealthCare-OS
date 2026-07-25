from rest_framework import serializers
from .models import JointAssessment, FractureRecord, PhysiotherapyPlan

class JointSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    class Meta:
        model = JointAssessment
        fields = ["id","patient","joint","side","assessment_date","range_of_motion","strength_grade","stability","pain_level","special_tests","findings","notes"]
        read_only_fields = ["id","performed_by"]

class FractureSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    class Meta:
        model = FractureRecord
        fields = ["id","patient","bone","fracture_type","classification","side","diagnosis_date","treatment","healing_status","follow_up_date","notes"]
        read_only_fields = ["id","diagnosed_by"]

class PhysioPlanSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    class Meta:
        model = PhysiotherapyPlan
        fields = ["id","patient","name","condition","exercises","start_date","end_date","is_active","notes"]
        read_only_fields = ["id","created_by"]
