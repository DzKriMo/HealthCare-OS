"""
Patient domain views: CRUD, search, timeline, related entities.

All endpoints are tenant-scoped and permission-gated.
"""
from django.db import models as db_models
from rest_framework import generics, status, views
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from drf_spectacular.utils import extend_schema

from tenancy.permissions import HasTenantAccess, TenantPermissionRequired
from .models import (
    Patient,
    MedicalHistory,
    Allergy,
    CurrentMedication,
    InsurancePolicy,
    EmergencyContact,
    ConsentRecord,
)
from . import serializers


# ═══════════════════════════════════════════════════════════════
# Patient CRUD
# ═══════════════════════════════════════════════════════════════

@extend_schema(tags=["patients"], summary="List and search patients")
class PatientListView(generics.ListCreateAPIView):
    """
    GET  — list patients (paginated), optionally search with ?q=
    POST — register a new patient
    """
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "patients.read"

    def get_serializer_class(self):
        if self.request.method == "POST":
            return serializers.PatientCreateSerializer
        return serializers.PatientListSerializer

    def get_queryset(self):
        qs = Patient.objects.for_tenant(self.request.tenant).filter(is_active=True)
        query = self.request.query_params.get("q", "")
        if query:
            qs = Patient.search(self.request.tenant, query)
        return qs.select_related("created_by").order_by("last_name", "first_name")


@extend_schema(tags=["patients"], summary="Patient detail, update, archive")
class PatientDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    — full patient detail with related entities
    PUT    — update patient demographics
    DELETE — soft-deactivate (archive)
    """
    permission_classes = [HasTenantAccess, TenantPermissionRequired]

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return serializers.PatientUpdateSerializer
        return serializers.PatientDetailSerializer

    def get_queryset(self):
        return Patient.objects.for_tenant(self.request.tenant)

    def get_required_permission(self):
        if self.request.method == "GET":
            return "patients.read"
        return "patients.write_demographics"

    def perform_destroy(self, instance):
        """Soft-deactivate rather than hard-delete."""
        instance.is_active = False
        instance.save(update_fields=["is_active"])


@extend_schema(tags=["patients"], summary="Search patients")
class PatientSearchView(generics.ListAPIView):
    """Search patients by name, phone, email, or ID. Use ?q= term."""
    serializer_class = serializers.PatientListSerializer
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "patients.read"

    def get_queryset(self):
        query = self.request.query_params.get("q", "")
        if not query or len(query) < 2:
            return Patient.objects.for_tenant(self.request.tenant).none()
        return Patient.search(self.request.tenant, query)[:25]


# ═══════════════════════════════════════════════════════════════
# Medical History
# ═══════════════════════════════════════════════════════════════

@extend_schema(tags=["patients"], summary="List/create medical history entries")
class MedicalHistoryListView(generics.ListCreateAPIView):
    serializer_class = serializers.MedicalHistorySerializer
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "patients.read"

    def get_serializer_class(self):
        if self.request.method == "POST":
            return serializers.MedicalHistoryCreateSerializer
        return serializers.MedicalHistorySerializer

    def get_queryset(self):
        patient_id = self.kwargs.get("patient_pk")
        return MedicalHistory.objects.for_tenant(self.request.tenant).filter(
            patient_id=patient_id,
        )


@extend_schema(tags=["patients"], summary="Update/delete medical history entry")
class MedicalHistoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = serializers.MedicalHistorySerializer
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "patients.write_demographics"

    def get_queryset(self):
        return MedicalHistory.objects.for_tenant(self.request.tenant)


# ═══════════════════════════════════════════════════════════════
# Allergies
# ═══════════════════════════════════════════════════════════════

@extend_schema(tags=["patients"], summary="List/create allergies")
class AllergyListView(generics.ListCreateAPIView):
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "patients.read"

    def get_serializer_class(self):
        if self.request.method == "POST":
            return serializers.AllergyCreateSerializer
        return serializers.AllergySerializer

    def get_queryset(self):
        patient_id = self.kwargs.get("patient_pk")
        return Allergy.objects.for_tenant(self.request.tenant).filter(
            patient_id=patient_id,
        )


@extend_schema(tags=["patients"], summary="Update/delete allergy")
class AllergyDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = serializers.AllergySerializer
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "patients.write_demographics"

    def get_queryset(self):
        return Allergy.objects.for_tenant(self.request.tenant)


# ═══════════════════════════════════════════════════════════════
# Medications
# ═══════════════════════════════════════════════════════════════

@extend_schema(tags=["patients"], summary="List/create medications")
class MedicationListView(generics.ListCreateAPIView):
    serializer_class = serializers.MedicationSerializer
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "patients.read"

    def get_queryset(self):
        patient_id = self.kwargs.get("patient_pk")
        return CurrentMedication.objects.for_tenant(self.request.tenant).filter(
            patient_id=patient_id,
        )

    def perform_create(self, serializer):
        serializer.save(tenant=self.request.tenant)


@extend_schema(tags=["patients"], summary="Update/delete medication")
class MedicationDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = serializers.MedicationSerializer
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "patients.write_demographics"

    def get_queryset(self):
        return CurrentMedication.objects.for_tenant(self.request.tenant)


# ═══════════════════════════════════════════════════════════════
# Insurance Policies
# ═══════════════════════════════════════════════════════════════

@extend_schema(tags=["patients"], summary="List/create insurance policies")
class InsurancePolicyListView(generics.ListCreateAPIView):
    serializer_class = serializers.InsurancePolicySerializer
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "patients.read"

    def get_queryset(self):
        patient_id = self.kwargs.get("patient_pk")
        return InsurancePolicy.objects.for_tenant(self.request.tenant).filter(
            patient_id=patient_id,
        )

    def perform_create(self, serializer):
        serializer.save(tenant=self.request.tenant)


@extend_schema(tags=["patients"], summary="Update/delete insurance policy")
class InsurancePolicyDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = serializers.InsurancePolicySerializer
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "patients.write_demographics"

    def get_queryset(self):
        return InsurancePolicy.objects.for_tenant(self.request.tenant)


# ═══════════════════════════════════════════════════════════════
# Emergency Contacts
# ═══════════════════════════════════════════════════════════════

@extend_schema(tags=["patients"], summary="List/create emergency contacts")
class EmergencyContactListView(generics.ListCreateAPIView):
    serializer_class = serializers.EmergencyContactSerializer
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "patients.read"

    def get_queryset(self):
        patient_id = self.kwargs.get("patient_pk")
        return EmergencyContact.objects.for_tenant(self.request.tenant).filter(
            patient_id=patient_id,
        )

    def perform_create(self, serializer):
        serializer.save(tenant=self.request.tenant)


@extend_schema(tags=["patients"], summary="Update/delete emergency contact")
class EmergencyContactDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = serializers.EmergencyContactSerializer
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "patients.write_demographics"

    def get_queryset(self):
        return EmergencyContact.objects.for_tenant(self.request.tenant)


# ═══════════════════════════════════════════════════════════════
# Consent Management
# ═══════════════════════════════════════════════════════════════

@extend_schema(tags=["patients"], summary="List/create consent records")
class ConsentListView(generics.ListCreateAPIView):
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "patients.read"

    def get_serializer_class(self):
        if self.request.method == "POST":
            return serializers.ConsentCreateSerializer
        return serializers.ConsentRecordSerializer

    def get_queryset(self):
        patient_id = self.kwargs.get("patient_pk")
        return ConsentRecord.objects.for_tenant(self.request.tenant).filter(
            patient_id=patient_id,
        )


@extend_schema(tags=["patients"], summary="Withdraw consent")
class ConsentWithdrawView(generics.GenericAPIView):
    """Withdraw a previously granted consent."""
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "patients.write_demographics"

    def post(self, request, pk):
        try:
            consent = ConsentRecord.objects.for_tenant(request.tenant).get(pk=pk)
        except ConsentRecord.DoesNotExist:
            raise NotFound("Consent record not found.")

        if consent.status != ConsentRecord.Status.GRANTED:
            return Response(
                {"error": "Only active consents can be withdrawn."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        reason = request.data.get("reason", "")
        consent.withdraw(reason)
        return Response({"detail": "Consent withdrawn."})


# ═══════════════════════════════════════════════════════════════
# Patient Timeline
# ═══════════════════════════════════════════════════════════════

@extend_schema(tags=["patients"], summary="Get patient timeline")
class PatientTimelineView(generics.GenericAPIView):
    """
    Unified chronological feed of all events for a patient.

    Aggregates: appointments, encounters, invoices, documents, notes,
    lab results, and consent changes — ordered by timestamp descending.
    """
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "patients.read"

    def get(self, request, patient_pk):
        # Verify patient exists and belongs to tenant
        try:
            patient = Patient.objects.for_tenant(request.tenant).get(pk=patient_pk)
        except Patient.DoesNotExist:
            raise NotFound("Patient not found.")

        timeline = self._build_timeline(patient, request.tenant)
        return Response(timeline)

    def _build_timeline(self, patient, tenant) -> list[dict]:
        """Build unified timeline from all relevant entities."""
        entries = []

        # Medical history entries
        for entry in patient.medical_history.all():
            entries.append({
                "id": str(entry.id),
                "type": "medical_history",
                "title": entry.condition,
                "description": entry.description or "",
                "timestamp": entry.recorded_at.isoformat(),
                "status": "active" if entry.is_active else "resolved",
                "metadata": {"category": entry.category, "version": entry.version},
            })

        # Allergies
        for allergy in patient.allergies.all():
            entries.append({
                "id": str(allergy.id),
                "type": "allergy",
                "title": f"{allergy.substance} ({allergy.severity})",
                "description": allergy.reaction or "",
                "timestamp": allergy.recorded_at.isoformat(),
                "status": allergy.status,
                "metadata": {"severity": allergy.severity},
            })

        # Medications
        for med in patient.medications.all():
            entries.append({
                "id": str(med.id),
                "type": "medication",
                "title": f"{med.drug_name} {med.dosage}",
                "description": f"Frequency: {med.frequency}. Route: {med.route}.",
                "timestamp": med.start_date.isoformat() if med.start_date else med.recorded_at.isoformat(),
                "status": "active" if med.is_active else "discontinued",
                "metadata": None,
            })

        # Consent records
        for consent in patient.consents.all():
            entries.append({
                "id": str(consent.id),
                "type": "consent",
                "title": f"{consent.get_consent_type_display()} — {consent.form_name}",
                "description": f"Version: {consent.form_version}. Status: {consent.status}.",
                "timestamp": consent.granted_at.isoformat(),
                "status": consent.status,
                "metadata": {"consent_type": consent.consent_type},
            })

        # Insurance policies
        for ins in patient.insurance_policies.all():
            entries.append({
                "id": str(ins.id),
                "type": "insurance",
                "title": f"{ins.provider} — {ins.get_coverage_type_display()}",
                "description": f"Policy: {ins.policy_number}. Active: {ins.is_active}.",
                "timestamp": ins.effective_date.isoformat(),
                "status": "active" if ins.is_active else "expired",
                "metadata": {"coverage_type": ins.coverage_type},
            })

        # Sort by timestamp descending
        entries.sort(key=lambda e: e["timestamp"], reverse=True)
        return entries
