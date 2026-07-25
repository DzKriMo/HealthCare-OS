"""Serializers for laboratory module."""
from rest_framework import serializers
from .models import TestCatalog, LabOrder, Specimen, LabResult


class TestCatalogSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)

    class Meta:
        model = TestCatalog
        fields = ["id","name","short_name","department","specimen_type","unit",
                  "reference_range_low","reference_range_high","reference_range_text",
                  "turnaround_minutes","price","is_active"]
        read_only_fields = ["id"]


class SpecimenSerializer(serializers.ModelSerializer):
    collected_by_name = serializers.CharField(source="collected_by.full_name", read_only=True)

    class Meta:
        model = Specimen
        fields = ["id","lab_order","barcode","specimen_type","collection_date",
                  "collected_by","collected_by_name","status","rejection_reason","notes"]
        read_only_fields = ["id","barcode","collected_by"]


class SpecimenCreateSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    barcode = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)

    class Meta:
        model = Specimen
        fields = ["id","barcode","status","lab_order","specimen_type","notes"]

    def create(self, validated_data):
        tenant = self.context["request"].tenant
        user = self.context["request"].user
        import secrets
        barcode = f"SPC-{secrets.token_hex(4).upper()}"
        return Specimen.objects.create(
            tenant=tenant, barcode=barcode, collected_by=user, **validated_data,
        )


class LabResultSerializer(serializers.ModelSerializer):
    test_name = serializers.CharField(source="test.name", read_only=True)
    department = serializers.CharField(source="test.department", read_only=True)
    unit = serializers.CharField(source="test.unit", read_only=True)
    reference = serializers.SerializerMethodField()
    performed_by_name = serializers.CharField(source="performed_by.full_name", read_only=True)

    class Meta:
        model = LabResult
        fields = ["id","lab_order","test","test_name","department","unit",
                  "value","value_text","flag","reference","status","is_critical",
                  "performed_by","performed_by_name","performed_at","notes"]
        read_only_fields = ["id","flag","is_critical","status","performed_by","performed_at"]

    def get_reference(self, obj):
        t = obj.test
        if t.reference_range_text:
            return t.reference_range_text
        low = str(t.reference_range_low) if t.reference_range_low else ""
        high = str(t.reference_range_high) if t.reference_range_high else ""
        return f"{low} - {high}" if low and high else ""


class LabResultCreateSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    flag = serializers.CharField(read_only=True)
    is_critical = serializers.BooleanField(read_only=True)
    status = serializers.CharField(read_only=True)

    class Meta:
        model = LabResult
        fields = ["id","flag","is_critical","status","lab_order","test","specimen","value","value_text","notes"]

    def create(self, validated_data):
        tenant = self.context["request"].tenant
        user = self.context["request"].user
        return LabResult.objects.create(tenant=tenant, performed_by=user, **validated_data)


class LabResultApproveSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=["review","approve","amend"])


class LabOrderSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    patient_name = serializers.CharField(source="patient.full_name", read_only=True)
    ordered_by_name = serializers.CharField(source="ordered_by.full_name", read_only=True)
    test_names = serializers.SerializerMethodField()

    class Meta:
        model = LabOrder
        fields = ["id","patient","patient_name","encounter","tests","test_names",
                  "status","priority","ordered_by","ordered_by_name","notes","ordered_at"]
        read_only_fields = ["id","status","ordered_by","ordered_at"]

    def get_test_names(self, obj):
        return [t.name for t in obj.tests.all()]


class LabOrderCreateSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    status = serializers.CharField(read_only=True)
    test_ids = serializers.ListField(child=serializers.UUIDField(), write_only=True)

    class Meta:
        model = LabOrder
        fields = ["id","status","patient","encounter","test_ids","priority","notes"]

    def create(self, validated_data):
        tenant = self.context["request"].tenant
        user = self.context["request"].user
        test_ids = validated_data.pop("test_ids", [])
        order = LabOrder.objects.create(tenant=tenant, ordered_by=user, **validated_data)
        order.tests.set(test_ids)
        return order
