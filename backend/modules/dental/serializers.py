"""Serializers for dental module."""
from rest_framework import serializers
from .models import (
    ToothChart, Tooth, ToothProcedure, Implant, Crown,
    DentalTreatmentPlan, TreatmentPlanPhase, PlannedProcedure,
)


class ToothSerializer(serializers.ModelSerializer):
    quadrant = serializers.CharField(read_only=True)
    is_primary = serializers.BooleanField(read_only=True)

    class Meta:
        model = Tooth
        fields = [
            "id", "fdi_number", "condition", "notes", "surface_data",
            "quadrant", "is_primary", "updated_at",
        ]
        read_only_fields = ["id", "updated_at"]


class ToothUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tooth
        fields = ["condition", "notes", "surface_data"]


class ToothChartSerializer(serializers.ModelSerializer):
    teeth = ToothSerializer(many=True, read_only=True)
    patient_name = serializers.CharField(source="patient.full_name", read_only=True)

    class Meta:
        model = ToothChart
        fields = ["id", "patient", "patient_name", "notes", "teeth", "updated_at"]
        read_only_fields = ["id", "updated_at"]


class ToothProcedureSerializer(serializers.ModelSerializer):
    fdi_number = serializers.IntegerField(source="tooth.fdi_number", read_only=True)
    performed_by_name = serializers.CharField(source="performed_by.full_name", read_only=True)

    class Meta:
        model = ToothProcedure
        fields = [
            "id", "tooth", "fdi_number", "patient", "appointment",
            "procedure_type", "surfaces", "description",
            "performed_by", "performed_by_name", "materials", "performed_at",
        ]
        read_only_fields = ["id", "performed_by", "performed_at"]


class ToothProcedureCreateSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    fdi_number = serializers.IntegerField(source="tooth.fdi_number", read_only=True)
    performed_by_name = serializers.CharField(source="performed_by.full_name", read_only=True)

    class Meta:
        model = ToothProcedure
        fields = [
            "id", "tooth", "fdi_number", "patient", "appointment",
            "procedure_type", "surfaces", "description", "materials",
            "performed_by_name", "performed_at",
        ]
        read_only_fields = ["id", "performed_at"]

    def create(self, validated_data):
        tenant = self.context["request"].tenant
        user = self.context["request"].user
        return ToothProcedure.objects.create(
            tenant=tenant, performed_by=user, **validated_data,
        )


class ImplantSerializer(serializers.ModelSerializer):
    fdi_number = serializers.IntegerField(source="tooth.fdi_number", read_only=True)

    class Meta:
        model = Implant
        fields = [
            "id", "tooth", "fdi_number", "patient",
            "brand", "model_name", "diameter_mm", "length_mm",
            "placement_date", "restoration_date", "notes",
        ]
        read_only_fields = ["id"]


class CrownSerializer(serializers.ModelSerializer):
    fdi_number = serializers.IntegerField(source="tooth.fdi_number", read_only=True)

    class Meta:
        model = Crown
        fields = [
            "id", "tooth", "fdi_number", "patient",
            "material", "prep_date", "cementation_date",
            "lab_name", "lab_tracking", "notes",
        ]
        read_only_fields = ["id"]


class PlannedProcedureSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlannedProcedure
        fields = [
            "id", "procedure_type", "tooth", "description",
            "priority", "estimated_cost", "is_completed",
        ]
        read_only_fields = ["id", "is_completed"]


class TreatmentPlanPhaseSerializer(serializers.ModelSerializer):
    procedures = PlannedProcedureSerializer(many=True, read_only=True)

    class Meta:
        model = TreatmentPlanPhase
        fields = ["id", "name", "order", "description", "is_completed", "estimated_cost", "procedures"]
        read_only_fields = ["id"]


class TreatmentPlanSerializer(serializers.ModelSerializer):
    phases = TreatmentPlanPhaseSerializer(many=True, read_only=True)
    patient_name = serializers.CharField(source="patient.full_name", read_only=True)
    created_by_name = serializers.CharField(source="created_by.full_name", read_only=True)

    class Meta:
        model = DentalTreatmentPlan
        fields = [
            "id", "patient", "patient_name", "name", "status",
            "notes", "phases",
            "estimated_total", "insurance_estimate", "patient_portion",
            "consent_signed", "consent_signed_at",
            "created_by", "created_by_name", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "status", "consent_signed", "consent_signed_at", "created_at", "updated_at"]


class TreatmentPlanCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DentalTreatmentPlan
        fields = ["patient", "name", "notes", "insurance_estimate"]

    def create(self, validated_data):
        tenant = self.context["request"].tenant
        user = self.context["request"].user
        return DentalTreatmentPlan.objects.create(
            tenant=tenant, created_by=user, **validated_data,
        )
