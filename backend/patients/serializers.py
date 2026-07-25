"""
Serializers for patient domain models.
"""
from rest_framework import serializers
from .models import (
    Patient,
    MedicalHistory,
    Allergy,
    CurrentMedication,
    InsurancePolicy,
    EmergencyContact,
    ConsentRecord,
)


# ── Patient ──────────────────────────────────────────────────

class PatientListSerializer(serializers.ModelSerializer):
    """Compact representation for list/search views."""
    full_name = serializers.CharField(read_only=True)
    age = serializers.IntegerField(read_only=True)

    class Meta:
        model = Patient
        fields = [
            "id", "display_id", "first_name", "last_name", "full_name",
            "age", "date_of_birth", "gender", "phone_primary",
            "city", "is_active", "registration_date",
        ]
        read_only_fields = ["id", "display_id", "registration_date"]


class PatientDetailSerializer(serializers.ModelSerializer):
    """Full patient detail including all related entities."""
    full_name = serializers.CharField(read_only=True)
    age = serializers.IntegerField(read_only=True)
    allergies = serializers.SerializerMethodField()
    emergency_contacts = serializers.SerializerMethodField()
    insurance_policies = serializers.SerializerMethodField()
    active_medications = serializers.SerializerMethodField()
    has_active_consents = serializers.SerializerMethodField()

    class Meta:
        model = Patient
        fields = [
            "id", "tenant", "display_id",
            "first_name", "middle_name", "last_name", "full_name",
            "date_of_birth", "age", "gender", "blood_type", "marital_status",
            "national_id_type",
            "phone_primary", "phone_secondary", "email",
            "address_line1", "address_line2", "city", "state", "postal_code", "country",
            "is_active", "registration_date",
            "allergies", "emergency_contacts", "insurance_policies",
            "active_medications", "has_active_consents",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "tenant", "display_id", "registration_date", "created_at", "updated_at"]

    def get_allergies(self, obj):
        return AllergySerializer(
            obj.allergies.filter(status="active"), many=True,
        ).data

    def get_emergency_contacts(self, obj):
        return EmergencyContactSerializer(
            obj.emergency_contacts.all(), many=True,
        ).data

    def get_insurance_policies(self, obj):
        return InsurancePolicySerializer(
            obj.insurance_policies.all(), many=True,
        ).data

    def get_active_medications(self, obj):
        return MedicationSerializer(
            obj.medications.filter(is_active=True), many=True,
        ).data

    def get_has_active_consents(self, obj) -> bool:
        return obj.consents.filter(status="granted").exists()


class PatientCreateSerializer(serializers.ModelSerializer):
    """Create a new patient — tenant is set automatically."""
    display_id = serializers.CharField(read_only=True)
    id = serializers.UUIDField(read_only=True)

    class Meta:
        model = Patient
        fields = [
            "id", "display_id",
            "first_name", "middle_name", "last_name",
            "date_of_birth", "gender", "blood_type", "marital_status",
            "national_id", "national_id_type",
            "phone_primary", "phone_secondary", "email",
            "address_line1", "address_line2", "city", "state", "postal_code", "country",
        ]

    def create(self, validated_data):
        tenant = self.context["request"].tenant
        user = self.context["request"].user

        # Generate display_id
        import datetime
        year = datetime.date.today().year
        count = Patient.objects.for_tenant(tenant).filter(
            registration_date__year=year,
        ).count()
        display_id = f"PAT-{year}-{count + 1:04d}"

        return Patient.objects.create(
            tenant=tenant,
            display_id=display_id,
            created_by=user,
            **validated_data,
        )


class PatientUpdateSerializer(serializers.ModelSerializer):
    """Update patient demographics — does not change tenant or display_id."""

    class Meta:
        model = Patient
        fields = [
            "first_name", "middle_name", "last_name",
            "date_of_birth", "gender", "blood_type", "marital_status",
            "national_id", "national_id_type",
            "phone_primary", "phone_secondary", "email",
            "address_line1", "address_line2", "city", "state", "postal_code", "country",
            "is_active",
        ]


# ── Medical History ──────────────────────────────────────────

class MedicalHistorySerializer(serializers.ModelSerializer):
    recorded_by_name = serializers.CharField(
        source="recorded_by.full_name", read_only=True,
    )

    class Meta:
        model = MedicalHistory
        fields = [
            "id", "patient", "category", "condition", "description",
            "onset_date", "resolved_date", "is_active",
            "version", "recorded_by", "recorded_by_name", "recorded_at",
        ]
        read_only_fields = ["id", "version", "recorded_by", "recorded_at"]


class MedicalHistoryCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicalHistory
        fields = [
            "patient", "category", "condition", "description",
            "onset_date", "resolved_date", "is_active",
        ]

    def create(self, validated_data):
        tenant = self.context["request"].tenant
        user = self.context["request"].user
        return MedicalHistory.objects.create(
            tenant=tenant,
            recorded_by=user,
            **validated_data,
        )


# ── Allergy ──────────────────────────────────────────────────

class AllergySerializer(serializers.ModelSerializer):
    class Meta:
        model = Allergy
        fields = [
            "id", "patient", "substance", "reaction", "severity",
            "onset_date", "status", "recorded_at", "updated_at",
        ]
        read_only_fields = ["id", "recorded_at", "updated_at"]


class AllergyCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Allergy
        fields = ["patient", "substance", "reaction", "severity", "onset_date", "status"]

    def create(self, validated_data):
        tenant = self.context["request"].tenant
        user = self.context["request"].user
        return Allergy.objects.create(
            tenant=tenant,
            recorded_by=user,
            **validated_data,
        )


# ── Medication ───────────────────────────────────────────────

class MedicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = CurrentMedication
        fields = [
            "id", "patient", "drug_name", "dosage", "frequency",
            "route", "start_date", "end_date", "prescribed_by",
            "is_active", "notes",
        ]
        read_only_fields = ["id"]


# ── Insurance Policy ─────────────────────────────────────────

class InsurancePolicySerializer(serializers.ModelSerializer):
    is_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = InsurancePolicy
        fields = [
            "id", "patient", "provider", "policy_number", "group_number",
            "coverage_type", "plan_name", "effective_date", "expiration_date",
            "policy_holder_name", "policy_holder_relationship",
            "is_verified", "is_active",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "is_verified", "created_at", "updated_at"]


# ── Emergency Contact ────────────────────────────────────────

class EmergencyContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmergencyContact
        fields = [
            "id", "patient", "name", "relationship",
            "phone_primary", "phone_secondary", "email",
            "address", "is_primary",
        ]
        read_only_fields = ["id"]


# ── Consent ──────────────────────────────────────────────────

class ConsentRecordSerializer(serializers.ModelSerializer):
    granted_by_name = serializers.CharField(
        source="granted_by.full_name", read_only=True,
    )

    class Meta:
        model = ConsentRecord
        fields = [
            "id", "patient", "consent_type", "form_name", "form_version",
            "status", "notes", "granted_at", "granted_by", "granted_by_name",
            "withdrawn_at", "withdrawal_reason", "expires_at",
        ]
        read_only_fields = ["id", "granted_at", "withdrawn_at"]


class ConsentCreateSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    status = serializers.CharField(read_only=True)
    granted_by_name = serializers.CharField(source="granted_by.full_name", read_only=True)

    class Meta:
        model = ConsentRecord
        fields = [
            "id", "patient", "consent_type", "form_name", "form_version",
            "status", "notes", "granted_at", "granted_by_name", "expires_at",
        ]
        read_only_fields = ["id", "status", "granted_at"]

    def create(self, validated_data):
        from django.utils import timezone
        tenant = self.context["request"].tenant
        user = self.context["request"].user
        request = self.context["request"]

        return ConsentRecord.objects.create(
            tenant=tenant,
            granted_by=user,
            granted_at=timezone.now(),
            ip_address=request.META.get("REMOTE_ADDR"),
            device_info=request.META.get("HTTP_USER_AGENT", ""),
            **validated_data,
        )


# ── Patient Timeline ─────────────────────────────────────────

class TimelineEntrySerializer(serializers.Serializer):
    """Unified patient timeline entry."""
    id = serializers.UUIDField()
    type = serializers.CharField()  # appointment, encounter, invoice, document, etc.
    title = serializers.CharField()
    description = serializers.CharField(allow_blank=True)
    timestamp = serializers.DateTimeField()
    status = serializers.CharField(allow_blank=True)
    metadata = serializers.DictField(allow_null=True)
