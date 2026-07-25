"""Serializers for pharmacy module."""
from rest_framework import serializers
from .models import Prescription, DispenseRecord, ControlledSubstanceLog


class PrescriptionListSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.full_name", read_only=True)
    prescribed_by_name = serializers.CharField(source="prescribed_by.full_name", read_only=True)
    refills_remaining = serializers.IntegerField(read_only=True)

    class Meta:
        model = Prescription
        fields = [
            "id", "patient", "patient_name", "drug_name", "dosage", "frequency",
            "status", "quantity_prescribed", "quantity_dispensed",
            "refills_authorized", "refills_remaining",
            "is_controlled", "controlled_schedule",
            "prescribed_by", "prescribed_by_name", "issued_date", "expiry_date",
        ]


class PrescriptionDetailSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.full_name", read_only=True)
    prescribed_by_name = serializers.CharField(source="prescribed_by.full_name", read_only=True)
    refills_remaining = serializers.IntegerField(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    dispense_records = serializers.SerializerMethodField()

    class Meta:
        model = Prescription
        fields = [
            "id", "patient", "patient_name", "encounter",
            "drug_name", "drug_code", "inventory_item",
            "dosage", "frequency", "duration_days", "route", "instructions",
            "quantity_prescribed", "quantity_dispensed",
            "refills_authorized", "refills_remaining", "daw",
            "is_controlled", "controlled_schedule",
            "status", "issued_date", "expiry_date", "is_expired",
            "prescribed_by", "prescribed_by_name", "notes",
            "created_at", "dispense_records",
        ]
        read_only_fields = ["id", "status", "quantity_dispensed", "prescribed_by", "created_at"]

    def get_dispense_records(self, obj):
        return DispenseRecordSerializer(
            obj.dispense_records.all()[:5], many=True,
        ).data


class PrescriptionCreateSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    status = serializers.CharField(read_only=True)

    class Meta:
        model = Prescription
        fields = [
            "id", "status", "patient", "encounter", "drug_name", "drug_code", "inventory_item",
            "dosage", "frequency", "duration_days", "route", "instructions",
            "quantity_prescribed", "refills_authorized", "daw",
            "is_controlled", "controlled_schedule", "notes", "expiry_date",
        ]

    def create(self, validated_data):
        tenant = self.context["request"].tenant
        user = self.context["request"].user
        return Prescription.objects.create(
            tenant=tenant, prescribed_by=user, status=Prescription.Status.ISSUED,
            issued_date=timezone.now().date(), **validated_data,
        )


from django.utils import timezone


class DispenseRecordSerializer(serializers.ModelSerializer):
    drug_name = serializers.CharField(source="prescription.drug_name", read_only=True)
    dispensed_by_name = serializers.CharField(source="dispensed_by.full_name", read_only=True)
    patient_name = serializers.CharField(source="patient.full_name", read_only=True)

    class Meta:
        model = DispenseRecord
        fields = [
            "id", "prescription", "patient", "patient_name",
            "drug_name", "quantity", "batch", "inventory_item",
            "copay_charged", "is_refill", "refill_number",
            "dispensed_by", "dispensed_by_name", "dispensed_at", "notes",
        ]
        read_only_fields = ["id", "dispensed_by", "dispensed_at"]


class DispenseCreateSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)

    class Meta:
        model = DispenseRecord
        fields = [
            "id", "prescription", "patient", "quantity", "batch",
            "inventory_item", "copay_charged", "is_refill", "refill_number", "notes",
        ]

    def validate(self, attrs):
        rx = attrs["prescription"]
        if rx.status == Prescription.Status.CANCELLED:
            raise serializers.ValidationError("Cannot dispense a cancelled prescription.")
        if rx.is_expired:
            raise serializers.ValidationError("Prescription has expired.")
        if attrs.get("is_refill") and rx.refills_remaining <= 0:
            raise serializers.ValidationError("No refills remaining.")
        return attrs

    def create(self, validated_data):
        tenant = self.context["request"].tenant
        user = self.context["request"].user
        return DispenseRecord.objects.create(
            tenant=tenant, dispensed_by=user, **validated_data,
        )


class ControlledLogSerializer(serializers.ModelSerializer):
    drug_name = serializers.CharField(source="prescription.drug_name", read_only=True)
    dispensed_by_name = serializers.CharField(source="dispense_record.dispensed_by.full_name", read_only=True)
    witness_name = serializers.CharField(source="witness.full_name", read_only=True)

    class Meta:
        model = ControlledSubstanceLog
        fields = [
            "id", "dispense_record", "prescription", "drug_name",
            "dispensed_by_name", "witness", "witness_name",
            "quantity_before_dispense", "quantity_after_dispense",
            "count_verified", "notes", "logged_at",
        ]
