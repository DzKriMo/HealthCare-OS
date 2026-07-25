"""
FHIR R4 API endpoints — Patient, Observation, Encounter, MedicationRequest.
FHIR-conformant with search parameters and Bundle responses.
"""
from django.db import models as db_models
from rest_framework import generics, status, views
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.exceptions import NotFound
from drf_spectacular.utils import extend_schema

from tenancy.permissions import HasTenantAccess
from patients.models import Patient as PatientModel
from clinical.models import Encounter, VitalSigns
from pharmacy.models import Prescription
from laboratory.models import LabResult
from .serializers import (
    FHIRPatientSerializer, FHIRObservationSerializer,
    FHIREncounterSerializer, FHIRMedicationRequestSerializer, FHIRBundleSerializer
)


@extend_schema(tags=["fhir"])
class FHIRPatientView(views.APIView):
    """FHIR Patient endpoint — GET /fhir/Patient/{id}"""
    permission_classes = [AllowAny]

    def get(self, request, pk=None):
        tenant = getattr(request, "tenant", None)
        if pk:
            try:
                if tenant:
                    patient = PatientModel.objects.for_tenant(tenant).get(pk=pk)
                else:
                    patient = PatientModel.objects.get(pk=pk)
            except PatientModel.DoesNotExist:
                raise NotFound("Patient not found")
            return Response(FHIRPatientSerializer.to_fhir(patient))

        # Search
        qs = PatientModel.objects.for_tenant(tenant) if tenant else PatientModel.objects.all()
        name = request.query_params.get("name")
        if name: qs = qs.filter(db_models.Q(first_name__icontains=name) | db_models.Q(last_name__icontains=name))
        birthdate = request.query_params.get("birthdate")
        if birthdate: qs = qs.filter(date_of_birth=birthdate)
        total = qs.count(); page = int(request.query_params.get("page", 1))
        patients = qs[(page-1)*20:page*20]
        entries = [FHIRPatientSerializer.to_fhir(p) for p in patients]
        return Response(FHIRBundleSerializer.search_bundle(entries, total, page))


@extend_schema(tags=["fhir"])
class FHIRObservationView(views.APIView):
    """FHIR Observation endpoint — GET /fhir/Observation"""
    permission_classes = [AllowAny]

    def get(self, request):
        tenant = getattr(request, "tenant", None)
        category = request.query_params.get("category","")
        patient_id = request.query_params.get("patient")
        entries = []

        if category == "vital-signs" and patient_id:
            vitals = VitalSigns.objects.for_tenant(tenant).filter(patient_id=patient_id)[:20] if tenant else []
            for v in vitals:
                entries.extend(FHIRObservationSerializer.from_vitals(v))
        elif category == "laboratory" and patient_id:
            labs = LabResult.objects.for_tenant(tenant).filter(lab_order__patient_id=patient_id)[:50] if tenant else []
            for lab in labs:
                entries.append(FHIRObservationSerializer.from_lab_result(lab))

        return Response(FHIRBundleSerializer.search_bundle(entries, len(entries)))


@extend_schema(tags=["fhir"])
class FHIREncounterView(views.APIView):
    """FHIR Encounter endpoint — GET /fhir/Encounter/{id}"""
    permission_classes = [AllowAny]

    def get(self, request, pk=None):
        tenant = getattr(request, "tenant", None)
        if pk:
            try:
                if tenant:
                    enc = Encounter.objects.for_tenant(tenant).get(pk=pk)
                else:
                    enc = Encounter.objects.get(pk=pk)
            except Encounter.DoesNotExist:
                raise NotFound("Encounter not found")
            return Response(FHIREncounterSerializer.to_fhir(enc))
        qs = Encounter.objects.for_tenant(tenant) if tenant else Encounter.objects.all()
        patient_id = request.query_params.get("patient")
        if patient_id: qs = qs.filter(patient_id=patient_id)
        total = qs.count()
        entries = [FHIREncounterSerializer.to_fhir(e) for e in qs[:20]]
        return Response(FHIRBundleSerializer.search_bundle(entries, total))


@extend_schema(tags=["fhir"])
class FHIRMedicationRequestView(views.APIView):
    """FHIR MedicationRequest endpoint."""
    permission_classes = [AllowAny]

    def get(self, request, pk=None):
        tenant = getattr(request, "tenant", None)
        if pk:
            try:
                if tenant:
                    rx = Prescription.objects.for_tenant(tenant).get(pk=pk)
                else:
                    rx = Prescription.objects.get(pk=pk)
            except Prescription.DoesNotExist:
                raise NotFound("MedicationRequest not found")
            return Response(FHIRMedicationRequestSerializer.to_fhir(rx))
        qs = Prescription.objects.for_tenant(tenant) if tenant else Prescription.objects.all()
        patient_id = request.query_params.get("patient")
        if patient_id: qs = qs.filter(patient_id=patient_id)
        total = qs.count()
        entries = [FHIRMedicationRequestSerializer.to_fhir(r) for r in qs[:20]]
        return Response(FHIRBundleSerializer.search_bundle(entries, total))


@extend_schema(tags=["fhir"])
class FHIRMetadataView(views.APIView):
    """FHIR CapabilityStatement — GET /fhir/metadata"""
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        return Response({
            "resourceType": "CapabilityStatement",
            "status": "active",
            "date": "2026-07-24",
            "publisher": "Healthcare OS",
            "kind": "instance",
            "software": {"name": "Healthcare OS FHIR Server", "version": "1.0.0"},
            "fhirVersion": "4.0.1",
            "format": ["json"],
            "rest": [{
                "mode": "server",
                "resource": [
                    {"type": "Patient", "profile": "http://hl7.org/fhir/StructureDefinition/Patient",
                     "interaction": [{"code": "read"},{"code": "search-type"}]},
                    {"type": "Observation", "profile": "http://hl7.org/fhir/StructureDefinition/Observation",
                     "interaction": [{"code": "search-type"}]},
                    {"type": "Encounter", "profile": "http://hl7.org/fhir/StructureDefinition/Encounter",
                     "interaction": [{"code": "read"},{"code": "search-type"}]},
                    {"type": "MedicationRequest", "profile": "http://hl7.org/fhir/StructureDefinition/MedicationRequest",
                     "interaction": [{"code": "read"},{"code": "search-type"}]},
                ],
            }],
        })

from django.db import models as db_models
import django.db.models as models
