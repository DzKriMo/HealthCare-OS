"""Tests for FHIR API endpoints."""
import pytest; from rest_framework.test import APIClient; from rest_framework import status
from tenancy.models import Tenant; from patients.models import Patient

@pytest.fixture
def tenant(db):
    t = Tenant.objects.create(name="TC", slug="fc")
    Patient.objects.create(tenant=t, first_name="John", last_name="Doe", display_id="P-FHIR", date_of_birth="1980-06-15", phone_primary="+1234567890", address_line1="123 Main", city="NYC", country="US")
    return t

@pytest.fixture
def api_client(): return APIClient()

@pytest.mark.django_db
class TestFHIR:
    def test_metadata(self, api_client):
        resp = api_client.get("/fhir/metadata")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["resourceType"] == "CapabilityStatement"

    def test_patient_search(self, api_client, tenant):
        resp = api_client.get("/fhir/Patient")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["resourceType"] == "Bundle"
        assert data["type"] == "searchset"

    def test_patient_by_id(self, api_client, tenant):
        patient = Patient.objects.first()
        resp = api_client.get(f"/fhir/Patient/{patient.id}")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["resourceType"] == "Patient"
        assert resp.json()["name"][0]["family"] == "Doe"

    def test_patient_search_by_name(self, api_client, tenant):
        resp = api_client.get("/fhir/Patient?name=Doe")
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.json()["entry"]) >= 1

    def test_patient_to_fhir_format(self, tenant):
        patient = Patient.objects.first()
        from fhir.serializers import FHIRPatientSerializer
        fhir_data = FHIRPatientSerializer.to_fhir(patient)
        assert fhir_data["resourceType"] == "Patient"
        assert fhir_data["birthDate"] == "1980-06-15"
        assert fhir_data["address"][0]["city"] == "NYC"
