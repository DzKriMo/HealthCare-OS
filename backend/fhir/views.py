from django.db import models as db_models
from rest_framework import generics, status, views
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.exceptions import NotFound
from drf_spectacular.utils import extend_schema
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from tenancy.permissions import HasTenantAccess
from patients.models import Patient as PatientModel, Allergy as AllergyModel, InsurancePolicy
from clinical.models import Encounter, VitalSigns, Diagnosis, Vaccination, MedicalHistory
from pharmacy.models import Prescription
from laboratory.models import LabResult, LabOrder
from inventory.models import InventoryItem
from identity.models import User
from .serializers import (
    FHIRPatientSerializer, FHIRObservationSerializer,
    FHIREncounterSerializer, FHIRMedicationRequestSerializer,
    FHIRAllergyIntoleranceSerializer, FHIRConditionSerializer,
    FHIRImmunizationSerializer, FHIRPractitionerSerializer,
    FHIRCoverageSerializer, FHIRDiagnosticReportSerializer,
    FHIRMedicationSerializer,
    bundle, operation_outcome,
)


class BaseFHIRView(views.APIView):
    permission_classes = [AllowAny]

    def get_tenant(self, request):
        return getattr(request, "tenant", None)

    def error(self, msg: str, code: str = "not-found", status_code: int = 404):
        return Response(operation_outcome("error", code, msg), status=status_code)


class FHIRResourceMixin:
    resource_type: str = ""
    serializer_class = None


@extend_schema(tags=["fhir"])
class FHIRPatientView(BaseFHIRView):
    resource_type = "Patient"

    def get(self, request, pk=None):
        tenant = self.get_tenant(request)
        if pk:
            try:
                patient = PatientModel.objects.for_tenant(tenant).get(pk=pk) if tenant else PatientModel.objects.get(pk=pk)
            except PatientModel.DoesNotExist:
                return self.error("Patient not found")
            return Response(FHIRPatientSerializer.to_fhir(patient))
        qs = PatientModel.objects.for_tenant(tenant) if tenant else PatientModel.objects.all()
        name = request.query_params.get("name")
        if name:
            qs = qs.filter(db_models.Q(first_name__icontains=name) | db_models.Q(last_name__icontains=name))
        birthdate = request.query_params.get("birthdate")
        if birthdate:
            qs = qs.filter(date_of_birth=birthdate)
        identifier = request.query_params.get("identifier")
        if identifier:
            qs = qs.filter(db_models.Q(display_id__iexact=identifier) | db_models.Q(id__iexact=identifier))
        total = qs.count()
        page = int(request.query_params.get("page", 1))
        patients = qs[(page - 1) * 20:page * 20]
        return Response(bundle([FHIRPatientSerializer.to_fhir(p) for p in patients], total, page))

    def post(self, request):
        tenant = self.get_tenant(request)
        if not tenant:
            return self.error("Tenant required", "forbidden", 403)
        data = FHIRPatientSerializer.from_fhir(request.data, tenant)
        patient = PatientModel.objects.create(tenant=tenant, **data)
        return Response(FHIRPatientSerializer.to_fhir(patient), status=201)

    def put(self, request, pk):
        tenant = self.get_tenant(request)
        try:
            patient = PatientModel.objects.for_tenant(tenant).get(pk=pk) if tenant else PatientModel.objects.get(pk=pk)
        except PatientModel.DoesNotExist:
            return self.error("Patient not found")
        data = FHIRPatientSerializer.from_fhir(request.data, tenant)
        for key, val in data.items():
            setattr(patient, key, val)
        patient.save()
        return Response(FHIRPatientSerializer.to_fhir(patient))


@extend_schema(tags=["fhir"])
class FHIRObservationView(BaseFHIRView):
    resource_type = "Observation"

    def get(self, request):
        tenant = self.get_tenant(request)
        category = request.query_params.get("category", "")
        patient_id = request.query_params.get("patient")
        entries = []
        if category == "vital-signs" and patient_id:
            vitals = VitalSigns.objects.for_tenant(tenant).filter(patient_id=patient_id)[:50] if tenant else []
            entries = [o for v in vitals for o in FHIRObservationSerializer.from_vitals(v)]
        elif category == "laboratory" and patient_id:
            labs = LabResult.objects.for_tenant(tenant).filter(lab_order__patient_id=patient_id)[:100] if tenant else []
            entries = [FHIRObservationSerializer.from_lab_result(l) for l in labs]
        return Response(bundle(entries, len(entries)))


@extend_schema(tags=["fhir"])
class FHIREncounterView(BaseFHIRView):
    resource_type = "Encounter"

    def get(self, request, pk=None):
        tenant = self.get_tenant(request)
        if pk:
            try:
                enc = Encounter.objects.for_tenant(tenant).get(pk=pk) if tenant else Encounter.objects.get(pk=pk)
            except Encounter.DoesNotExist:
                return self.error("Encounter not found")
            return Response(FHIREncounterSerializer.to_fhir(enc))
        qs = Encounter.objects.for_tenant(tenant) if tenant else Encounter.objects.all()
        patient_id = request.query_params.get("patient")
        if patient_id:
            qs = qs.filter(patient_id=patient_id)
        date = request.query_params.get("date")
        if date:
            qs = qs.filter(created_at__date=date)
        total = qs.count()
        return Response(bundle([FHIREncounterSerializer.to_fhir(e) for e in qs[:50]], total))


@extend_schema(tags=["fhir"])
class FHIRMedicationRequestView(BaseFHIRView):
    resource_type = "MedicationRequest"

    def get(self, request, pk=None):
        tenant = self.get_tenant(request)
        if pk:
            try:
                rx = Prescription.objects.for_tenant(tenant).get(pk=pk) if tenant else Prescription.objects.get(pk=pk)
            except Prescription.DoesNotExist:
                return self.error("MedicationRequest not found")
            return Response(FHIRMedicationRequestSerializer.to_fhir(rx))
        qs = Prescription.objects.for_tenant(tenant) if tenant else Prescription.objects.all()
        patient_id = request.query_params.get("patient")
        if patient_id:
            qs = qs.filter(patient_id=patient_id)
        status = request.query_params.get("status")
        if status:
            qs = qs.filter(status=status)
        total = qs.count()
        return Response(bundle([FHIRMedicationRequestSerializer.to_fhir(r) for r in qs[:50]], total))


@extend_schema(tags=["fhir"])
class FHIRAllergyIntoleranceView(BaseFHIRView):
    resource_type = "AllergyIntolerance"

    def get(self, request, pk=None):
        tenant = self.get_tenant(request)
        if pk:
            try:
                allergy = AllergyModel.objects.for_tenant(tenant).get(pk=pk) if tenant else AllergyModel.objects.get(pk=pk)
            except AllergyModel.DoesNotExist:
                return self.error("AllergyIntolerance not found")
            return Response(FHIRAllergyIntoleranceSerializer.to_fhir(allergy))
        qs = AllergyModel.objects.for_tenant(tenant) if tenant else AllergyModel.objects.all()
        patient_id = request.query_params.get("patient")
        if patient_id:
            qs = qs.filter(patient_id=patient_id)
        total = qs.count()
        return Response(bundle([FHIRAllergyIntoleranceSerializer.to_fhir(a) for a in qs[:50]], total))


@extend_schema(tags=["fhir"])
class FHIRConditionView(BaseFHIRView):
    resource_type = "Condition"

    def get(self, request, pk=None):
        tenant = self.get_tenant(request)
        if pk:
            try:
                diagnosis = Diagnosis.objects.for_tenant(tenant).get(pk=pk) if tenant else Diagnosis.objects.get(pk=pk)
            except Diagnosis.DoesNotExist:
                return self.error("Condition not found")
            return Response(FHIRConditionSerializer.to_fhir(diagnosis))
        entries = []
        patient_id = request.query_params.get("patient")
        if patient_id:
            diagnoses = Diagnosis.objects.for_tenant(tenant).filter(patient_id=patient_id) if tenant else Diagnosis.objects.filter(patient_id=patient_id)
            entries = [FHIRConditionSerializer.to_fhir(d) for d in diagnoses[:50]]
            histories = MedicalHistory.objects.for_tenant(tenant).filter(patient_id=patient_id) if tenant else MedicalHistory.objects.filter(patient_id=patient_id)
            entries.extend(FHIRConditionSerializer.from_medical_history(h) for h in histories[:20])
        return Response(bundle(entries, len(entries)))


@extend_schema(tags=["fhir"])
class FHIRImmunizationView(BaseFHIRView):
    resource_type = "Immunization"

    def get(self, request, pk=None):
        tenant = self.get_tenant(request)
        if pk:
            try:
                vax = Vaccination.objects.for_tenant(tenant).get(pk=pk) if tenant else Vaccination.objects.get(pk=pk)
            except Vaccination.DoesNotExist:
                return self.error("Immunization not found")
            return Response(FHIRImmunizationSerializer.to_fhir(vax))
        qs = Vaccination.objects.for_tenant(tenant) if tenant else Vaccination.objects.all()
        patient_id = request.query_params.get("patient")
        if patient_id:
            qs = qs.filter(patient_id=patient_id)
        total = qs.count()
        return Response(bundle([FHIRImmunizationSerializer.to_fhir(v) for v in qs[:50]], total))


@extend_schema(tags=["fhir"])
class FHIRPractitionerView(BaseFHIRView):
    resource_type = "Practitioner"

    def get(self, request, pk=None):
        if pk:
            try:
                user = User.objects.get(pk=pk)
            except User.DoesNotExist:
                return self.error("Practitioner not found")
            return Response(FHIRPractitionerSerializer.to_fhir(user))
        tenant = self.get_tenant(request)
        qs = User.objects.filter(is_active=True)
        if tenant:
            qs = qs.filter(tenant=tenant)
        specialty = request.query_params.get("specialty")
        if specialty:
            qs = qs.filter(specialty__icontains=specialty)
        total = qs.count()
        return Response(bundle([FHIRPractitionerSerializer.to_fhir(u) for u in qs[:50]], total))


@extend_schema(tags=["fhir"])
class FHIRCoverageView(BaseFHIRView):
    resource_type = "Coverage"

    def get(self, request, pk=None):
        tenant = self.get_tenant(request)
        if pk:
            try:
                policy = InsurancePolicy.objects.for_tenant(tenant).get(pk=pk) if tenant else InsurancePolicy.objects.get(pk=pk)
            except InsurancePolicy.DoesNotExist:
                return self.error("Coverage not found")
            return Response(FHIRCoverageSerializer.to_fhir(policy))
        qs = InsurancePolicy.objects.for_tenant(tenant) if tenant else InsurancePolicy.objects.all()
        patient_id = request.query_params.get("patient")
        if patient_id:
            qs = qs.filter(patient_id=patient_id)
        total = qs.count()
        return Response(bundle([FHIRCoverageSerializer.to_fhir(p) for p in qs[:50]], total))


@extend_schema(tags=["fhir"])
class FHIRDiagnosticReportView(BaseFHIRView):
    resource_type = "DiagnosticReport"

    def get(self, request, pk=None):
        tenant = self.get_tenant(request)
        if pk:
            try:
                order = LabOrder.objects.for_tenant(tenant).get(pk=pk) if tenant else LabOrder.objects.get(pk=pk)
            except LabOrder.DoesNotExist:
                return self.error("DiagnosticReport not found")
            return Response(FHIRDiagnosticReportSerializer.to_fhir(order))
        qs = LabOrder.objects.for_tenant(tenant) if tenant else LabOrder.objects.all()
        patient_id = request.query_params.get("patient")
        if patient_id:
            qs = qs.filter(patient_id=patient_id)
        total = qs.count()
        return Response(bundle([FHIRDiagnosticReportSerializer.to_fhir(o) for o in qs[:50]], total))


@extend_schema(tags=["fhir"])
class FHIRMedicationView(BaseFHIRView):
    resource_type = "Medication"

    def get(self, request, pk=None):
        tenant = self.get_tenant(request)
        if pk:
            try:
                item = InventoryItem.objects.for_tenant(tenant).get(pk=pk, category__in=["medication"]) if tenant else InventoryItem.objects.get(pk=pk)
            except InventoryItem.DoesNotExist:
                return self.error("Medication not found")
            return Response(FHIRMedicationSerializer.to_fhir(item))
        qs = InventoryItem.objects.for_tenant(tenant).filter(is_active=True) if tenant else InventoryItem.objects.filter(is_active=True)
        category = request.query_params.get("category", "medication")
        if category:
            qs = qs.filter(category=category)
        total = qs.count()
        return Response(bundle([FHIRMedicationSerializer.to_fhir(i) for i in qs[:50]], total))


@extend_schema(tags=["fhir"])
class FHIRMetadataView(BaseFHIRView):
    authentication_classes = []

    def get(self, request):
        resources = [
            {"type": "Patient", "profile": "http://hl7.org/fhir/StructureDefinition/Patient", "interaction": [{"code": "read"}, {"code": "search-type"}, {"code": "create"}, {"code": "update"}]},
            {"type": "Observation", "profile": "http://hl7.org/fhir/StructureDefinition/Observation", "interaction": [{"code": "search-type"}]},
            {"type": "Encounter", "profile": "http://hl7.org/fhir/StructureDefinition/Encounter", "interaction": [{"code": "read"}, {"code": "search-type"}]},
            {"type": "MedicationRequest", "profile": "http://hl7.org/fhir/StructureDefinition/MedicationRequest", "interaction": [{"code": "read"}, {"code": "search-type"}]},
            {"type": "AllergyIntolerance", "profile": "http://hl7.org/fhir/StructureDefinition/AllergyIntolerance", "interaction": [{"code": "read"}, {"code": "search-type"}]},
            {"type": "Condition", "profile": "http://hl7.org/fhir/StructureDefinition/Condition", "interaction": [{"code": "read"}, {"code": "search-type"}]},
            {"type": "Immunization", "profile": "http://hl7.org/fhir/StructureDefinition/Immunization", "interaction": [{"code": "read"}, {"code": "search-type"}]},
            {"type": "Practitioner", "profile": "http://hl7.org/fhir/StructureDefinition/Practitioner", "interaction": [{"code": "read"}, {"code": "search-type"}]},
            {"type": "Coverage", "profile": "http://hl7.org/fhir/StructureDefinition/Coverage", "interaction": [{"code": "read"}, {"code": "search-type"}]},
            {"type": "DiagnosticReport", "profile": "http://hl7.org/fhir/StructureDefinition/DiagnosticReport", "interaction": [{"code": "read"}, {"code": "search-type"}]},
            {"type": "Medication", "profile": "http://hl7.org/fhir/StructureDefinition/Medication", "interaction": [{"code": "read"}, {"code": "search-type"}]},
        ]
        return Response({
            "resourceType": "CapabilityStatement",
            "status": "active",
            "date": "2026-07-25",
            "publisher": "Healthcare OS",
            "kind": "instance",
            "software": {"name": "Healthcare OS FHIR Server", "version": "1.1.0"},
            "fhirVersion": "4.0.1",
            "format": ["json"],
            "rest": [{"mode": "server", "resource": resources,
                      "security": {"cors": True, "service": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/restful-security-service", "code": "SMART-on-FHIR"}]}]}}],
        })
