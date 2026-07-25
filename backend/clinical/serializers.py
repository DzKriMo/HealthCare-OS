"""Serializers for clinical module."""
from rest_framework import serializers
from .models import Encounter, Diagnosis, Referral, VitalSigns, Vaccination, FamilyHistory, SocialHistory


class EncounterSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    patient_name = serializers.CharField(source="patient.full_name", read_only=True)
    practitioner_name = serializers.CharField(source="practitioner.full_name", read_only=True)

    class Meta:
        model = Encounter
        fields = ["id","patient","patient_name","appointment","subjective","objective","assessment","plan",
                  "status","encounter_date","duration_minutes","practitioner","practitioner_name","signed_at","created_at"]
        read_only_fields = ["id","status","practitioner","signed_at","created_at"]

    def create(self, v):
        v["tenant"] = self.context["request"].tenant
        v["practitioner"] = self.context["request"].user
        return Encounter.objects.create(**v)


class DiagnosisSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    recorded_by_name = serializers.CharField(source="recorded_by.full_name", read_only=True)

    class Meta:
        model = Diagnosis
        fields = ["id","patient","encounter","icd_code","description","diagnosis_type","is_chronic","onset_date","resolved_date","is_active","notes","recorded_by","recorded_by_name"]
        read_only_fields = ["id","recorded_by"]

    def create(self, v):
        v["tenant"] = self.context["request"].tenant
        v["recorded_by"] = self.context["request"].user
        return Diagnosis.objects.create(**v)


class ReferralSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)

    class Meta:
        model = Referral
        fields = ["id","patient","encounter","specialist_name","specialty","reason","urgency","status","notes","created_at"]
        read_only_fields = ["id","status","created_at"]

    def create(self, v):
        v["tenant"] = self.context["request"].tenant
        v["referring_practitioner"] = self.context["request"].user
        return Referral.objects.create(**v)


class VitalSignsSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    class Meta:
        model = VitalSigns
        fields = ["id","patient","encounter","systolic_bp","diastolic_bp","heart_rate","respiratory_rate",
                  "temperature_c","oxygen_saturation","height_cm","weight_kg","bmi","pain_score","recorded_at","notes"]
        read_only_fields = ["id","bmi","recorded_at"]


class VaccinationSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    class Meta:
        model = Vaccination
        fields = ["id","patient","vaccine_name","dose_number","lot_number","administration_site","administered_date","next_due_date","notes"]
        read_only_fields = ["id"]


class FamilyHistorySerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    class Meta:
        model = FamilyHistory
        fields = ["id","patient","relationship","condition","age_at_onset","status","notes"]
        read_only_fields = ["id"]


class SocialHistorySerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    class Meta:
        model = SocialHistory
        fields = ["id","patient","smoking_status","alcohol_use","exercise_frequency","occupation","diet_description","notes"]
        read_only_fields = ["id"]
